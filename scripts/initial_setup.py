"""
Initial System Setup & Historical Backfill Script.
Initializes SQLite database, syncs stock master and classifications,
performs resumable backfill of historical market data and benchmark,
and computes all technical metrics, money flow scores, and rotation histories.

Usage:
    python scripts/initial_setup.py --days 30
    python scripts/initial_setup.py --days 250
"""

import sys
import argparse
import logging
import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import Database
from providers.nse_provider import NSEProvider
from pipeline.update_classification import ClassificationUpdater
from pipeline.update_market_data import MarketDataUpdater
from analytics.stock_metrics import StockMetricsCalculator
from analytics.industry_metrics import IndustryMetricsCalculator
from analytics.scoring import MoneyFlowScorer
from analytics.rotation import RotationDetector
from config.settings import DEFAULT_BACKFILL_DAYS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("initial_setup")


def run_initial_setup(days: int = DEFAULT_BACKFILL_DAYS, force: bool = False):
    print("=" * 60)
    print(" INDIAN STOCK MARKET INDUSTRY MONEY FLOW - INITIAL SETUP")
    print("=" * 60)
    start_time = datetime.datetime.now()
    
    db = Database()
    provider = NSEProvider()
    
    # 1. Initialize DB Schema
    print("\n[Step 1/6] Initializing Database Schema...")
    db.initialize_schema()
    
    # 2. Sync Universe & Classifications
    print("\n[Step 2/6] Syncing NSE Stock Universe & Industry Classifications...")
    class_updater = ClassificationUpdater(db=db, provider=provider)
    synced_stocks = class_updater.sync_universe_and_classifications()
    print(f"-> {synced_stocks} listed equity securities synced.")
    
    # 3. Calculate Date Range for Backfill
    print(f"\n[Step 3/6] Ingesting {days} Trading Sessions of Market & Delivery Data...")
    end_date = datetime.date.today()
    # Estimate calendar days needed to cover trading days (~1.5x trading days for weekends/holidays)
    start_date = end_date - datetime.timedelta(days=int(days * 1.55))
    
    market_updater = MarketDataUpdater(db=db, provider=provider)
    backfill_res = market_updater.backfill_date_range(start_date=start_date, end_date=end_date, force=force)
    
    print(f"-> Expected trading days: {backfill_res['trading_days_total']}")
    print(f"-> Ingested sessions:     {backfill_res['missing_dates_downloaded']}")
    print(f"-> Daily price records:   {backfill_res['records_inserted']}")
    print(f"-> Benchmark records:     {backfill_res['benchmark_records']}")
    if backfill_res['failed_dates']:
        print(f"-> Skipped/Failed dates:  {backfill_res['failed_dates']}")
        
    # 4. Stock-Level Analytics
    print("\n[Step 4/6] Calculating Stock Technical Metrics (Returns, EMAs, RS, Breakouts)...")
    stock_calc = StockMetricsCalculator(db=db)
    sm_count = stock_calc.calculate_all_stock_metrics()
    print(f"-> {sm_count} stock metric records computed.")
    
    # 5. Industry Aggregation & Breadth
    print("\n[Step 5/6] Aggregating Granular Industry Metrics & Breadth...")
    ind_calc = IndustryMetricsCalculator(db=db)
    im_count = ind_calc.calculate_all_industry_metrics()
    print(f"-> {im_count} industry metric records aggregated.")
    
    # 6. Scoring & Rotation
    print("\n[Step 6/6] Computing Money Flow Scores, Leadership, & Rotation States...")
    scorer = MoneyFlowScorer(db=db)
    scorer.calculate_industry_money_flow_scores()
    scorer.calculate_stock_leadership_scores()
    
    rot_detector = RotationDetector(db=db)
    rot_detector.calculate_rotation_states()
    
    elapsed = datetime.datetime.now() - start_time
    
    # Summary
    latest_date = db.get_latest_trading_date()
    df_latest_ind = db.get_latest_industry_metrics(trade_date=latest_date)
    
    print("\n" + "=" * 60)
    print(f" SETUP COMPLETED SUCCESSFULLY (Duration: {elapsed.total_seconds():.1f}s)")
    print("=" * 60)
    print(f"Latest Trading Date: {latest_date}")
    
    if not df_latest_ind.empty:
        top_ind = df_latest_ind.iloc[0]
        print(f"\nTop Money Flow Industry:")
        print(f"  {top_ind['basic_industry']} | Score: {top_ind['score_today']} | Status: {top_ind['status']} | 5D Ret: {top_ind['avg_return_5d']:+.1f}%")
        
        df_emg = df_latest_ind[df_latest_ind['status'] == 'EMERGING'].sort_values('score_change_5d', ascending=False)
        if not df_emg.empty:
            top_emg = df_emg.iloc[0]
            print(f"\nTop Emerging Industry:")
            print(f"  {top_emg['basic_industry']} | Score: {top_emg['score_today']} | 5D Score Accel: {top_emg['score_change_5d']:+.1f}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initial Setup & Backfill for Indian Stock Market Money Flow Screener")
    parser.add_argument("--days", type=int, default=DEFAULT_BACKFILL_DAYS, help="Number of historical trading days to backfill (default: 250)")
    parser.add_argument("--force", action="store_true", help="Force redownload of already ingested dates")
    args = parser.parse_args()
    
    run_initial_setup(days=args.days, force=args.force)
