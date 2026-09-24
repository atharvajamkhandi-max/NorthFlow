"""
Daily Pipeline Runner with 4-Checkpoint Retry Strategy & Idempotency.
Checkpoints: 17:00, 18:00, 19:00, 20:00 IST (Asia/Kolkata).
Features:
- Idempotency: Exits immediately if today's session is already successfully processed.
- Trading Day Detection: Skips weekends and NSE holidays.
- Checkpoint Retry: Retries at 17:00, 18:00, 19:00. Marks FAILED/STALE only after 20:00.
"""

import sys
import logging
import datetime
from typing import Dict, Any, Optional, Union
import pandas as pd

from database.db import Database
from providers.nse_provider import NSEProvider
from pipeline.update_market_data import MarketDataUpdater
from analytics.stock_metrics import StockMetricsCalculator
from analytics.industry_metrics import IndustryMetricsCalculator
from analytics.scoring import MoneyFlowScorer
from analytics.rotation import RotationDetector
from config.settings import DAILY_UPDATE_TIMES, TIMEZONE

logger = logging.getLogger(__name__)


class DailyPipelineRunner:
    """
    Orchestrates daily pipeline execution at configured checkpoints.
    """

    def __init__(self, db: Optional[Database] = None, provider: Optional[NSEProvider] = None):
        self.db = db or Database()
        self.provider = provider or NSEProvider()

    def is_trading_day(self, check_date: datetime.date) -> bool:
        """
        Determines whether check_date is an official NSE trading day (weekday and not an exchange holiday).
        """
        if check_date.weekday() >= 5:  # Saturday (5) or Sunday (6)
            return False

        # Query provider's trading calendar
        start_cal = check_date - datetime.timedelta(days=7)
        trading_days = self.provider.get_trading_days(start_cal, check_date)
        iso_str = check_date.strftime("%Y-%m-%d")
        return iso_str in trading_days

    def is_already_processed_today(self, trade_date: str) -> bool:
        """
        Checks whether trade_date has already been successfully ingested and processed.
        """
        with self.db.get_connection() as conn:
            # Check price records existence
            price_count = conn.execute("SELECT COUNT(*) FROM daily_prices WHERE date = ?;", [trade_date]).fetchone()[0]
            if price_count == 0:
                return False

            # Check pipeline success log
            log_row = conn.execute(
                "SELECT id FROM pipeline_logs WHERE stage = 'DAILY_PIPELINE_COMPLETE' AND status = 'SUCCESS' AND trade_date = ? LIMIT 1;",
                [trade_date]
            ).fetchone()
            return log_row is not None

    @staticmethod
    def get_ist_now() -> datetime.datetime:
        """Returns current datetime in Indian Standard Time (UTC+5:30)."""
        try:
            import zoneinfo
            return datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata"))
        except Exception:
            return datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)

    def get_latest_completed_trading_day(self, as_of: Optional[datetime.datetime] = None) -> datetime.date:
        """
        Returns the latest official NSE trading day whose market session has completed
        (i.e. after 16:30 IST). If current time is before 16:30 IST, returns previous trading day.
        """
        if as_of is None:
            as_of = self.get_ist_now()

        # If before market close / data publishing (16:30 IST), target yesterday or earlier
        if as_of.time() < datetime.time(16, 30):
            candidate = as_of.date() - datetime.timedelta(days=1)
        else:
            candidate = as_of.date()

        start_cal = candidate - datetime.timedelta(days=14)
        trading_days = self.provider.get_trading_days(start_cal, candidate)
        if trading_days:
            return datetime.datetime.strptime(trading_days[-1], "%Y-%m-%d").date()
        return candidate

    def determine_current_checkpoint(self, now_time: Optional[datetime.time] = None) -> str:
        """
        Determines the current checkpoint label (e.g. '17:00', '18:00', '19:00', '20:00') based on time.
        """
        if now_time is None:
            now_time = self.get_ist_now().time()

        t_str = now_time.strftime("%H:%M")
        if t_str < "17:30":
            return "17:00"
        elif t_str < "18:30":
            return "18:00"
        elif t_str < "19:30":
            return "19:00"
        else:
            return "20:00"

    def run_checkpoint(
        self,
        target_date: Optional[Union[str, datetime.date]] = None,
        checkpoint_time_str: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Executes a checkpoint run for target_date.
        If target_date is None, auto-detects the latest completed trading day and
        automatically catches up any missing trading sessions between the DB and target_date.
        """
        self.db.initialize_schema()
        now_dt = self.get_ist_now()

        if checkpoint_time_str is None:
            checkpoint_time_str = self.determine_current_checkpoint(now_dt.time())

        # Determine dates to process
        if target_date is not None:
            if isinstance(target_date, str):
                target_date_obj = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
            else:
                target_date_obj = target_date
            dates_to_process = [target_date_obj.strftime("%Y-%m-%d")]
        else:
            target_date_obj = self.get_latest_completed_trading_day(now_dt)
            iso_target = target_date_obj.strftime("%Y-%m-%d")

            # Check if there are missing trading days between DB max date and target_date
            with self.db.get_connection() as conn:
                row = conn.execute("SELECT MAX(date) FROM daily_prices;").fetchone()
                max_db_date_str = row[0] if row and row[0] else None

            if max_db_date_str and not force:
                if max_db_date_str >= iso_target:
                    if self.is_already_processed_today(iso_target):
                        msg = f"Latest market data ({iso_target}) already processed successfully. No action required."
                        logger.info(msg)
                        self.db.log_pipeline_event(
                            stage="DAILY_PIPELINE_CHECKPOINT",
                            status="SKIPPED",
                            trade_date=iso_target,
                            records_processed=0,
                            message=msg
                        )
                        return {
                            "status": "SKIPPED_ALREADY_SUCCESS",
                            "trade_date": iso_target,
                            "checkpoint": checkpoint_time_str,
                            "records_processed": 0,
                            "message": msg
                        }
                    else:
                        dates_to_process = [iso_target]
                else:
                    max_db_date = datetime.datetime.strptime(max_db_date_str, "%Y-%m-%d").date()
                    trading_days = self.provider.get_trading_days(max_db_date, target_date_obj)
                    dates_to_process = [d for d in trading_days if d > max_db_date_str and d <= iso_target]
                    if not dates_to_process:
                        dates_to_process = [iso_target]
            else:
                dates_to_process = [iso_target]

        logger.info(f"Initiating Daily Pipeline Checkpoint [{checkpoint_time_str} IST] for Trade Date(s): {dates_to_process}")

        market_updater = MarketDataUpdater(db=self.db, provider=self.provider)
        total_inserted = 0
        successfully_ingested_dates = []

        for d_str in dates_to_process:
            d_obj = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
            if not force and not self.is_trading_day(d_obj):
                logger.info(f"Skipping {d_str} (not an official trading day).")
                continue

            logger.info(f"Attempting NSE market data download for {d_str} at checkpoint {checkpoint_time_str} IST...")
            inserted_prices = market_updater.ingest_single_date(d_str, force=force)

            with self.db.get_connection() as conn:
                count_today = conn.execute("SELECT COUNT(*) FROM daily_prices WHERE date = ?;", [d_str]).fetchone()[0]

            if count_today > 0:
                total_inserted += inserted_prices
                successfully_ingested_dates.append(d_str)
                start_lookback = d_obj - datetime.timedelta(days=7)
                market_updater.sync_benchmark_data(start_lookback, d_obj)
            else:
                logger.warning(f"NSE market data unavailable for {d_str} at checkpoint {checkpoint_time_str} IST.")

        if not successfully_ingested_dates:
            is_final_checkpoint = (checkpoint_time_str == "20:00" or checkpoint_time_str == DAILY_UPDATE_TIMES[-1])
            iso_date = dates_to_process[-1]
            if is_final_checkpoint:
                fail_msg = f"PIPELINE FAILED / DATA STALE: NSE market data unavailable after final {checkpoint_time_str} IST attempt for {iso_date}."
                logger.error(fail_msg)
                self.db.log_pipeline_event(
                    stage="DAILY_PIPELINE_COMPLETE",
                    status="FAILED",
                    trade_date=iso_date,
                    records_processed=0,
                    message=fail_msg
                )
                return {
                    "status": "FAILED",
                    "trade_date": iso_date,
                    "checkpoint": checkpoint_time_str,
                    "records_processed": 0,
                    "message": fail_msg
                }
            else:
                retry_msg = f"NSE market data unavailable at {checkpoint_time_str} IST attempt. Next retry scheduled at later checkpoint."
                logger.warning(retry_msg)
                self.db.log_pipeline_event(
                    stage="DAILY_PIPELINE_CHECKPOINT",
                    status="RETRY_PENDING",
                    trade_date=iso_date,
                    records_processed=0,
                    message=retry_msg
                )
                return {
                    "status": "RETRY_PENDING",
                    "trade_date": iso_date,
                    "checkpoint": checkpoint_time_str,
                    "records_processed": 0,
                    "message": retry_msg
                }

        # Data is available -> Process complete analytical pipeline across dataset
        logger.info(f"NSE data available for {len(successfully_ingested_dates)} date(s) ({total_inserted} new records). Processing full analytical pipeline...")

        logger.info("Computing stock metrics...")
        stock_calc = StockMetricsCalculator(db=self.db)
        stock_calc.calculate_all_stock_metrics()

        logger.info("Aggregating industry breadth & metrics...")
        ind_calc = IndustryMetricsCalculator(db=self.db)
        ind_calc.calculate_all_industry_metrics()

        logger.info("Scoring Money Flow & Stock Leadership...")
        scorer = MoneyFlowScorer(db=self.db)
        scorer.calculate_industry_money_flow_scores()
        scorer.calculate_stock_leadership_scores()

        logger.info("Detecting Industry Rotation States...")
        rot = RotationDetector(db=self.db)
        rot.calculate_rotation_states()

        # Auto-classify any new IPOs / newly listed symbols
        try:
            from pipeline.ipo_classifier import classify_new_ipos
            with self.db.get_connection() as conn:
                ipo_result = classify_new_ipos(conn)
            if ipo_result["classified"] > 0:
                logger.info(
                    f"IPO Auto-Classifier: {ipo_result['classified']} new symbols classified, "
                    f"{ipo_result['unclassified']} flagged for manual review."
                )
        except Exception as e:
            logger.warning(f"IPO auto-classifier encountered an error (non-fatal): {e}")

        # Log completion for each successfully ingested date
        for d_str in successfully_ingested_dates:
            with self.db.get_connection() as conn:
                count_d = conn.execute("SELECT COUNT(*) FROM daily_prices WHERE date = ?;", [d_str]).fetchone()[0]
            success_msg = f"Daily pipeline completed successfully at {checkpoint_time_str} IST for {d_str} ({count_d} equities processed)."
            self.db.log_pipeline_event(
                stage="DAILY_PIPELINE_COMPLETE",
                status="SUCCESS",
                trade_date=d_str,
                records_processed=count_d,
                message=success_msg
            )

        latest_completed_date = successfully_ingested_dates[-1]
        summary_msg = f"Daily pipeline completed successfully for {len(successfully_ingested_dates)} date(s) ending {latest_completed_date} ({total_inserted} records ingested)."
        logger.info(summary_msg)

        return {
            "status": "SUCCESS",
            "trade_date": latest_completed_date,
            "checkpoint": checkpoint_time_str,
            "records_processed": total_inserted,
            "message": summary_msg
        }
