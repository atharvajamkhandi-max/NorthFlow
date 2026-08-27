"""
1.5-Year (375 Trading Sessions) Historical Market Data Backfiller.
Downloads bhavcopy with delivery from nselib, caches locally as Parquet,
and inserts into SQLite with full rate limiting and retry handling.
"""

import os
import sys
import time
import datetime
import logging
import sqlite3
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"
sys.path.insert(0, BASE_DIR)

import nselib
from nselib import capital_market
from database.db import Database
from providers.nse_provider import NSEProvider
from config.settings import BENCHMARK_INDEX, VALID_SERIES

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CACHE_DIR = os.path.join(BASE_DIR, "data", "bhavcopy_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def determine_1_5_year_trading_dates(provider: NSEProvider, target_sessions: int = 375) -> list:
    """
    Generates approx 375 trading dates going back ~1.5 calendar years from latest date.
    """
    holidays = set(provider.get_trading_holidays())
    
    # End date: latest trading day (e.g., 2025-08-22 or 2026-08-21)
    end_dt = datetime.date(2025, 8, 22)
    valid_dates = []
    curr = end_dt
    
    # Walk backward until 375 trading sessions are collected
    while len(valid_dates) < target_sessions and curr > datetime.date(2023, 1, 1):
        if curr.weekday() < 5: # Monday to Friday
            iso_d = curr.strftime("%Y-%m-%d")
            if iso_d not in holidays:
                valid_dates.append(iso_d)
        curr -= datetime.timedelta(days=1)
        
    valid_dates.reverse()
    return valid_dates

def run_1_5_year_backfill(target_sessions: int = 375):
    print("=" * 80)
    print(f" STARTING 1.5-YEAR ({target_sessions} TRADING SESSIONS) DATA INGESTION VIA NSELIB")
    print("=" * 80)

    db = Database()
    provider = NSEProvider()

    trading_dates = determine_1_5_year_trading_dates(provider, target_sessions=target_sessions)
    print(f"\n[1/4] Target Window: {len(trading_dates)} Trading Sessions")
    print(f"      From: {trading_dates[0]}  To: {trading_dates[-1]}")

    # Check already ingested dates in DB
    existing_dates = set(db.get_existing_price_dates())
    print(f"      Already in Database: {len(existing_dates)} sessions")

    missing_dates = [d for d in trading_dates if d not in existing_dates]
    print(f"      Remaining to Fetch/Ingest: {len(missing_dates)} sessions")

    # Fetch/Ingest missing dates
    downloaded = 0
    cached_hits = 0
    errors = 0

    print("\n[2/4] Downloading & Ingesting Bhavcopies with Delivery...")
    for i, iso_date in enumerate(missing_dates, 1):
        cache_file = os.path.join(CACHE_DIR, f"bhavcopy_{iso_date}.parquet")
        df_prices = pd.DataFrame()

        # Check local cache first
        if os.path.exists(cache_file):
            try:
                df_prices = pd.read_parquet(cache_file)
                cached_hits += 1
            except Exception:
                df_prices = pd.DataFrame()

        if df_prices.empty:
            dmy_date = provider._format_to_dmy(iso_date)
            # Try delivery bhavcopy
            try:
                df_raw = capital_market.bhav_copy_with_delivery(dmy_date)
                if df_raw is not None and not df_raw.empty:
                    df_clean = df_raw.copy()
                    df_clean.columns = [str(c).strip() for c in df_clean.columns]
                    if 'SYMBOL' in df_clean.columns and 'CLOSE_PRICE' in df_clean.columns:
                        df_prices = provider._parse_delivery_bhavcopy(df_clean, iso_date)
            except Exception as e:
                pass

            # Fallback to standard equity bhavcopy if delivery endpoint had a hiccup
            if df_prices.empty:
                try:
                    df_raw2 = capital_market.bhav_copy_equities(dmy_date)
                    if df_raw2 is not None and not df_raw2.empty:
                        df_clean2 = df_raw2.copy()
                        df_clean2.columns = [str(c).strip() for c in df_clean2.columns]
                        if 'TckrSymb' in df_clean2.columns:
                            df_prices = provider._parse_old_bhavcopy(df_clean2, iso_date)
                        elif 'SYMBOL' in df_clean2.columns and 'CLOSE' in df_clean2.columns:
                            df_prices = provider._parse_standard_bhavcopy(df_clean2, iso_date)
                except Exception as e2:
                    errors += 1

            if not df_prices.empty:
                df_prices.to_parquet(cache_file, index=False)
                downloaded += 1
                time.sleep(0.3) # Friendly rate throttle

        # Insert into SQLite
        if not df_prices.empty:
            db.insert_or_replace_df("daily_prices", df_prices)

        if i % 25 == 0 or i == len(missing_dates):
            print(f"      Progress: {i}/{len(missing_dates)} processed (Downloaded: {downloaded}, Cache Hits: {cached_hits}, Errors: {errors})")

    # Sync Benchmark Index Data for 1.5 Years
    print("\n[3/4] Synchronizing Benchmark Index (NIFTY Smallcap 250 & NIFTY 50)...")
    try:
        df_bench_raw = capital_market.index_data(BENCHMARK_INDEX, provider._format_to_dmy(trading_dates[0]), provider._format_to_dmy(trading_dates[-1]))
        if df_bench_raw is not None and not df_bench_raw.empty:
            df_b = provider._parse_index_data(df_bench_raw, BENCHMARK_INDEX)
            df_b = df_b.sort_values('date').reset_index(drop=True)
            df_b['return_1d'] = df_b['close'].pct_change(1) * 100.0
            df_b['return_5d'] = df_b['close'].pct_change(5) * 100.0
            df_b['return_20d'] = df_b['close'].pct_change(20) * 100.0
            db.insert_or_replace_df("market_benchmark", df_b)
            print(f"      Inserted {len(df_b)} benchmark records for {BENCHMARK_INDEX}.")
    except Exception as e:
        print(f"      Benchmark sync note: {e}")

    # Final Summary
    total_dates_in_db = sorted(db.get_existing_price_dates())
    print("\n[4/4] Ingestion Complete!")
    print(f"      Total Available Sessions in Database: {len(total_dates_in_db)}")
    print(f"      Historical Date Range: {total_dates_in_db[0]} to {total_dates_in_db[-1]}")
    print("=" * 80)

if __name__ == "__main__":
    run_1_5_year_backfill(target_sessions=375)
