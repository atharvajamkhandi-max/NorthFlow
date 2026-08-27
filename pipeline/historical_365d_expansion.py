"""
Phase 13A: Resumable 365-Trading-Session Historical Data Acquisition Engine.
Uses nselib (bhav_copy_with_delivery and index_data) with local caching, throttling, retry logic,
and safe non-destructive database expansion.
"""

import os
import time
import shutil
import sqlite3
import datetime
import logging
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np

import nselib
from nselib import capital_market

from database.db import Database
from providers.nse_provider import NSEProvider
from config.settings import BENCHMARK_INDEX, VALID_SERIES

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "data", "bhavcopy_cache")
BACKUP_DB_PATH = os.path.join(BASE_DIR, "data", "market_flow_37d_backup.db")

class Historical365dExpansionEngine:
    def __init__(self, target_sessions: int = 365):
        self.target_sessions = target_sessions
        self.db = Database()
        self.provider = NSEProvider()
        os.makedirs(CACHE_DIR, exist_ok=True)

    def backup_existing_database(self):
        """Creates a safe immutable backup of the original 37-session database."""
        orig_db = self.db.db_path
        if os.path.exists(orig_db) and not os.path.exists(BACKUP_DB_PATH):
            shutil.copy2(orig_db, BACKUP_DB_PATH)
            logger.info(f"Backed up original database to {BACKUP_DB_PATH}")

    def determine_historical_trading_dates(self) -> List[str]:
        """
        Determines the exact historical date range required to obtain approximately
        the target 365 actual trading sessions based on NSE calendar.
        """
        holidays = set(self.provider.get_trading_holidays())
        
        # End at current/latest available date (e.g. 2025-08-22 or today)
        end_dt = datetime.date(2025, 8, 22)
        valid_trading_days = []
        curr = end_dt

        # Walk backward until target_sessions trading days are found
        while len(valid_trading_days) < self.target_sessions and curr > datetime.date(2023, 1, 1):
            if curr.weekday() < 5: # Mon-Fri
                curr_str = curr.strftime("%Y-%m-%d")
                if curr_str not in holidays:
                    valid_trading_days.append(curr_str)
            curr -= datetime.timedelta(days=1)

        valid_trading_days.reverse()
        logger.info(f"Target trading sessions: {len(valid_trading_days)} (Range: {valid_trading_days[0]} to {valid_trading_days[-1]})")
        return valid_trading_days

    def sync_benchmark_history(self, start_date: str, end_date: str) -> int:
        """
        Synchronizes historical benchmark index data for NIFTY Smallcap 250 across the full 365 sessions.
        """
        logger.info(f"Synchronizing benchmark ({BENCHMARK_INDEX}) from {start_date} to {end_date}...")
        dmy_start = self.provider._format_to_dmy(start_date)
        dmy_end = self.provider._format_to_dmy(end_date)
        
        df_bench = pd.DataFrame()
        try:
            df_raw = capital_market.index_data(BENCHMARK_INDEX, dmy_start, dmy_end)
            if df_raw is not None and not df_raw.empty:
                df_bench = self.provider._parse_index_data(df_raw, BENCHMARK_INDEX)
        except Exception as e:
            logger.warning(f"Failed to fetch {BENCHMARK_INDEX} via index_data: {e}. Attempting chunked fallback...")

        # Fallback or synthetic anchor if specific smallcap index history endpoint has gaps
        if df_bench.empty or len(df_bench) < 100:
            # Reconstruct from existing benchmark table or calculate synthetic smallcap proxy
            with self.db.get_connection() as conn:
                existing_bench = pd.read_sql_query("SELECT * FROM market_benchmark ORDER BY date ASC;", conn)
            if not existing_bench.empty:
                logger.info(f"Found {len(existing_bench)} existing benchmark records.")
                df_bench = existing_bench

        if not df_bench.empty:
            df_bench = df_bench.sort_values('date').reset_index(drop=True)
            df_bench['return_1d'] = df_bench['close'].pct_change(1) * 100.0
            df_bench['return_5d'] = df_bench['close'].pct_change(5) * 100.0
            df_bench['return_20d'] = df_bench['close'].pct_change(20) * 100.0
            count = self.db.insert_or_replace_df("market_benchmark", df_bench)
            logger.info(f"Inserted/updated {count} benchmark records for {BENCHMARK_INDEX}.")
            return count
        return 0

    def download_and_ingest_session(self, trade_date: str, retry_count: int = 3) -> int:
        """
        Downloads bhavcopy with delivery for a single date with local caching and retry logic.
        """
        cache_file = os.path.join(CACHE_DIR, f"bhavcopy_{trade_date}.parquet")
        df_prices = pd.DataFrame()

        # 1. Check local cache
        if os.path.exists(cache_file):
            try:
                df_prices = pd.read_parquet(cache_file)
            except Exception:
                df_prices = pd.DataFrame()

        # 2. If not cached, fetch via nselib
        if df_prices.empty:
            dmy_date = self.provider._format_to_dmy(trade_date)
            for attempt in range(retry_count):
                try:
                    df_raw = capital_market.bhav_copy_with_delivery(dmy_date)
                    if df_raw is not None and not df_raw.empty:
                        df_clean = df_raw.copy()
                        df_clean.columns = [str(c).strip() for c in df_clean.columns]
                        if 'SYMBOL' in df_clean.columns and 'CLOSE_PRICE' in df_clean.columns:
                            df_prices = self.provider._parse_delivery_bhavcopy(df_clean, trade_date)
                            break
                except Exception as e:
                    time.sleep(0.5 * (attempt + 1))
            
            # Fallback to standard equity bhavcopy if delivery endpoint times out
            if df_prices.empty:
                try:
                    df_raw2 = capital_market.bhav_copy_equities(dmy_date)
                    if df_raw2 is not None and not df_raw2.empty:
                        df_clean2 = df_raw2.copy()
                        df_clean2.columns = [str(c).strip() for c in df_clean2.columns]
                        if 'TckrSymb' in df_clean2.columns:
                            df_prices = self.provider._parse_old_bhavcopy(df_clean2, trade_date)
                        elif 'SYMBOL' in df_clean2.columns and 'CLOSE' in df_clean2.columns:
                            df_prices = self.provider._parse_standard_bhavcopy(df_clean2, trade_date)
                except Exception as e2:
                    logger.warning(f"Could not fetch data for date {trade_date}: {e2}")

            # Save to local cache if valid
            if not df_prices.empty:
                df_prices.to_parquet(cache_file, index=False)

        # 3. Ingest into SQLite database
        if not df_prices.empty:
            inserted = self.db.insert_or_replace_df("daily_prices", df_prices)
            return inserted
        return 0

    def run_expansion(self) -> Dict[str, Any]:
        """
        Executes the full 365-session expansion cycle.
        """
        self.backup_existing_database()
        trading_dates = self.determine_historical_trading_dates()
        
        # Check existing dates in daily_prices
        existing_dates = set(self.db.get_existing_price_dates())
        missing_dates = [d for d in trading_dates if d not in existing_dates]
        
        logger.info(f"Total Target Sessions: {len(trading_dates)} | Already in DB: {len(existing_dates)} | Missing to Fetch: {len(missing_dates)}")
        
        # Sync benchmark
        if trading_dates:
            self.sync_benchmark_history(trading_dates[0], trading_dates[-1])

        # Batch download / ingest missing dates
        downloaded = 0
        failed = 0
        for i, dt in enumerate(missing_dates):
            inserted = self.download_and_ingest_session(dt)
            if inserted > 0:
                downloaded += 1
                if downloaded % 25 == 0:
                    logger.info(f"Progress: Ingested {downloaded}/{len(missing_dates)} sessions...")
            else:
                failed += 1

        all_current_dates = sorted(self.db.get_existing_price_dates())
        logger.info(f"Expansion complete! Total Sessions in Database: {len(all_current_dates)} (Range: {all_current_dates[0]} to {all_current_dates[-1]})")

        return {
            'target_sessions': len(trading_dates),
            'total_sessions_in_db': len(all_current_dates),
            'first_date': all_current_dates[0] if all_current_dates else None,
            'latest_date': all_current_dates[-1] if all_current_dates else None,
            'downloaded_in_run': downloaded,
            'failed_dates': failed
        }
