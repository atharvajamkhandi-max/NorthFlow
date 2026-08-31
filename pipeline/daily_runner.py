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

    def determine_current_checkpoint(self, now_time: Optional[datetime.time] = None) -> str:
        """
        Determines the current checkpoint label (e.g. '17:00', '18:00', '19:00', '20:00') based on time.
        """
        if now_time is None:
            now_time = datetime.datetime.now().time()

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
        """
        self.db.initialize_schema()
        now_dt = datetime.datetime.now()

        if target_date is None:
            target_date = now_dt.date()
        elif isinstance(target_date, str):
            target_date = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()

        iso_date = target_date.strftime("%Y-%m-%d")
        if checkpoint_time_str is None:
            checkpoint_time_str = self.determine_current_checkpoint(now_dt.time())

        logger.info(f"Initiating Daily Pipeline Checkpoint [{checkpoint_time_str} IST] for Trade Date: {iso_date}")

        # 1. Trading Day Check
        if not force and not self.is_trading_day(target_date):
            msg = f"No trading session on {iso_date} (Weekend/Holiday). Pipeline skipped."
            logger.info(msg)
            self.db.log_pipeline_event(
                stage="DAILY_PIPELINE_CHECKPOINT",
                status="SKIPPED",
                trade_date=iso_date,
                records_processed=0,
                message=msg
            )
            return {
                "status": "SKIPPED_NOT_TRADING_DAY",
                "trade_date": iso_date,
                "checkpoint": checkpoint_time_str,
                "message": msg
            }

        # 2. Idempotency Check
        if not force and self.is_already_processed_today(iso_date):
            msg = f"Today's market data ({iso_date}) already processed successfully. No action required."
            logger.info(msg)
            self.db.log_pipeline_event(
                stage="DAILY_PIPELINE_CHECKPOINT",
                status="SKIPPED",
                trade_date=iso_date,
                records_processed=0,
                message=msg
            )
            return {
                "status": "SKIPPED_ALREADY_SUCCESS",
                "trade_date": iso_date,
                "checkpoint": checkpoint_time_str,
                "message": msg
            }

        # 3. Attempt Market Data Fetch
        logger.info(f"Attempting NSE market data download for {iso_date} at checkpoint {checkpoint_time_str} IST...")
        market_updater = MarketDataUpdater(db=self.db, provider=self.provider)
        inserted_prices = market_updater.ingest_single_date(iso_date, force=force)

        with self.db.get_connection() as conn:
            total_prices_today = conn.execute("SELECT COUNT(*) FROM daily_prices WHERE date = ?;", [iso_date]).fetchone()[0]

        # 4. If data is completely unavailable (neither newly inserted nor existing in DB)
        if total_prices_today == 0:
            is_final_checkpoint = (checkpoint_time_str == "20:00" or checkpoint_time_str == DAILY_UPDATE_TIMES[-1])
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
                    "message": retry_msg
                }

        # 5. Data is available -> Process complete pipeline immediately
        logger.info(f"NSE data available ({total_prices_today} records). Processing full analytical pipeline...")
        start_lookback = target_date - datetime.timedelta(days=7)
        market_updater.sync_benchmark_data(start_lookback, target_date)

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

        success_msg = f"Daily pipeline completed successfully at {checkpoint_time_str} IST for {iso_date} ({total_prices_today} equities processed)."
        logger.info(success_msg)
        self.db.log_pipeline_event(
            stage="DAILY_PIPELINE_COMPLETE",
            status="SUCCESS",
            trade_date=iso_date,
            records_processed=total_prices_today,
            message=success_msg
        )

        return {
            "status": "SUCCESS",
            "trade_date": iso_date,
            "checkpoint": checkpoint_time_str,
            "records_processed": inserted_prices,
            "message": success_msg
        }
