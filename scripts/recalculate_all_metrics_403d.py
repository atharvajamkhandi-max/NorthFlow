"""
Full Database Metrics Recalculator.
Populates stock_metrics, industry_metrics, money_flow_scores, and rotation_states
for all 403 historical trading sessions in SQLite.
"""

import sys
import os
import time
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.db import Database
from analytics.stock_metrics import StockMetricsCalculator
from analytics.industry_metrics import IndustryMetricsCalculator
from analytics.scoring import MoneyFlowScorer
from analytics.rotation import RotationDetector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    print("=" * 80)
    print(" RECALCULATING ALL DATABASE METRICS FOR ALL 403 HISTORICAL SESSIONS")
    print("=" * 80)

    db = Database()
    dates = db.get_existing_price_dates()
    print(f"\nProcessing metrics across {len(dates)} trading sessions ({dates[0]} to {dates[-1]})...")

    t0 = time.time()

    print("\n[1/4] Calculating stock metrics (RS, Momentum, EMAs, Volume, Delivery)...")
    stock_calc = StockMetricsCalculator(db=db)
    stock_calc.calculate_all_stock_metrics()

    print("\n[2/4] Aggregating industry breadth and metrics across 135 Basic Industries...")
    ind_calc = IndustryMetricsCalculator(db=db)
    ind_calc.calculate_all_industry_metrics()

    print("\n[3/4] Calculating Money Flow and Stock Leadership scores...")
    scorer = MoneyFlowScorer(db=db)
    scorer.calculate_industry_money_flow_scores()
    scorer.calculate_stock_leadership_scores()

    print("\n[4/4] Calculating Industry Rotation states...")
    rot = RotationDetector(db=db)
    rot.calculate_rotation_states()

    elapsed = time.time() - t0
    print("\n" + "=" * 80)
    print(f" ALL DATABASE METRICS POPULATED SUCCESSFULLY IN {elapsed:.1f}s")
    print("=" * 80)

if __name__ == "__main__":
    main()
