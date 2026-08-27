"""
Resumable Market Data Ingestion Pipeline.
Fetches daily equity bhavcopy with delivery and benchmark index data.
Skips already-ingested dates to support safe resumption and avoid redundant API requests.
"""

import logging
import datetime
from typing import List, Dict, Any, Optional, Union
import pandas as pd

from database.db import Database
from providers.nse_provider import NSEProvider
from config.settings import BENCHMARK_INDEX

logger = logging.getLogger(__name__)


class MarketDataUpdater:
    """
    Ingests and synchronizes daily market data (prices, volumes, delivery) and benchmark data into SQLite.
    """

    def __init__(self, db: Optional[Database] = None, provider: Optional[NSEProvider] = None):
        self.db = db or Database()
        self.provider = provider or NSEProvider()

    def sync_benchmark_data(self, start_date: Union[str, datetime.date], end_date: Union[str, datetime.date]) -> int:
        """
        Synchronizes historical benchmark index (NIFTY 50) prices.
        """
        iso_start = self.provider._format_to_iso(start_date)
        iso_end = self.provider._format_to_iso(end_date)
        
        logger.info(f"Syncing benchmark ({BENCHMARK_INDEX}) data from {iso_start} to {iso_end}...")
        df_bench = self.provider.get_index_data(index_name=BENCHMARK_INDEX, from_date=iso_start, to_date=iso_end)
        
        if df_bench.empty:
            logger.warning(f"No benchmark data returned for {BENCHMARK_INDEX} in range {iso_start} - {iso_end}")
            return 0

        # Calculate benchmark returns
        df_bench = df_bench.sort_values('date').reset_index(drop=True)
        if 'index_name' not in df_bench.columns or df_bench['index_name'].isnull().any():
            df_bench['index_name'] = BENCHMARK_INDEX
        df_bench['return_1d'] = df_bench['close'].pct_change(1) * 100.0
        df_bench['return_5d'] = df_bench['close'].pct_change(5) * 100.0
        if 'return_20d' not in df_bench.columns:
            df_bench['return_20d'] = df_bench['close'].pct_change(20) * 100.0
        # Filter to benchmark table schema
        bench_cols = ['date', 'index_name', 'open', 'high', 'low', 'close', 'return_1d', 'return_5d', 'return_20d']
        df_bench = df_bench[[c for c in bench_cols if c in df_bench.columns]]
        count = self.db.insert_or_replace_df("market_benchmark", df_bench)
        logger.info(f"Inserted/updated {count} benchmark records for {BENCHMARK_INDEX}.")
        return count

    def ingest_single_date(self, trade_date: Union[str, datetime.date], force: bool = False) -> int:
        """
        Ingests bhavcopy with delivery for a single trading date.
        """
        iso_date = self.provider._format_to_iso(trade_date)
        
        if not force:
            existing = set(self.db.get_existing_price_dates())
            if iso_date in existing:
                logger.info(f"Date {iso_date} already exists in daily_prices. Skipping.")
                return 0

        df_prices = self.provider.get_daily_equity_data(iso_date)
        if df_prices.empty:
            logger.warning(f"No valid equity prices returned for date {iso_date}")
            self.db.log_pipeline_event(
                stage="MARKET_DATA_INGESTION",
                status="WARNING",
                trade_date=iso_date,
                records_processed=0,
                message=f"No equity data returned for date {iso_date}"
            )
            return 0

        inserted = self.db.insert_or_replace_df("daily_prices", df_prices)
        self.db.log_pipeline_event(
            stage="MARKET_DATA_INGESTION",
            status="SUCCESS",
            trade_date=iso_date,
            records_processed=inserted,
            message=f"Ingested {inserted} daily price records for {iso_date}"
        )
        return inserted

    def backfill_date_range(self, start_date: Union[str, datetime.date], end_date: Union[str, datetime.date],
                            force: bool = False) -> Dict[str, Any]:
        """
        Resumable batch backfill for a date range.
        Skips already completed trading dates.
        """
        trading_days = self.provider.get_trading_days(start_date, end_date)
        logger.info(f"Identified {len(trading_days)} expected trading days between {start_date} and {end_date}.")

        existing_dates = set(self.db.get_existing_price_dates()) if not force else set()
        missing_dates = [d for d in trading_days if d not in existing_dates]
        
        logger.info(f"Found {len(missing_dates)} missing trading dates to download (already present: {len(existing_dates)}).")

        total_inserted = 0
        failed_dates = []

        for idx, t_date in enumerate(missing_dates, 1):
            logger.info(f"[{idx}/{len(missing_dates)}] Ingesting market data for {t_date}...")
            try:
                cnt = self.ingest_single_date(t_date, force=force)
                total_inserted += cnt
                if cnt == 0:
                    failed_dates.append(t_date)
            except Exception as e:
                logger.error(f"Error ingesting date {t_date}: {e}")
                failed_dates.append(t_date)

        # Sync benchmark data for full range
        bench_count = self.sync_benchmark_data(start_date, end_date)

        return {
            "trading_days_total": len(trading_days),
            "missing_dates_downloaded": len(missing_dates) - len(failed_dates),
            "records_inserted": total_inserted,
            "benchmark_records": bench_count,
            "failed_dates": failed_dates
        }
