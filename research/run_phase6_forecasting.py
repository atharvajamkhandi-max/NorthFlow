"""
Phase 6: Multi-Horizon Return Forecasting & Probability Calibration Master Runner.
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"
sys.path.insert(0, BASE_DIR)

from database.db import Database
from research.engine.factor_engine import compute_all_stock_factors
from research.engine.industry_factors import compute_industry_factor_matrix
from research.engine.forecasting_targets import compute_forecasting_targets
from research.engine.forecasting_validation import run_multi_horizon_walk_forward_evaluation
from research.engine.forecasting_reports import build_all_forecasting_reports

def main():
    print("=" * 75)
    print(" PHASE 6: MULTI-HORIZON RETURN FORECASTING & PROBABILITY CALIBRATION")
    print(" (STRICT RESEARCH ISOLATION - ZERO PRODUCTION MODIFICATIONS)")
    print("=" * 75)

    reports_dir = os.path.join(BASE_DIR, "research", "reports")
    results_dir = os.path.join(BASE_DIR, "research", "results")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # 1. Load Data
    print("\n[Step 1/4] Loading historical prices and benchmark from SQLite...")
    db = Database()
    with db.get_connection() as conn:
        df_prices = pd.read_sql_query("""
            SELECT dp.*, s.industry, s.basic_industry 
            FROM daily_prices dp
            JOIN stocks s ON dp.symbol = s.symbol
            WHERE s.active = 1 AND s.basic_industry != 'UNKNOWN'
            ORDER BY dp.symbol ASC, dp.date ASC;
        """, conn)
        df_bench = pd.read_sql_query("SELECT date, close FROM market_benchmark ORDER BY date ASC;", conn)

    # 2. Compute Factors and Targets
    print("\n[Step 2/4] Computing feature matrix and multi-horizon forward targets/excursions...")
    df_stk_factors = compute_all_stock_factors(df_prices, df_bench)
    df_ind_matrix = compute_industry_factor_matrix(df_stk_factors, df_bench)
    df_targets, _ = compute_forecasting_targets(df_prices, df_bench)

    # 3. Walk-Forward Forecast Validation
    print("\n[Step 3/4] Running multi-horizon walk-forward validation and calibration...")
    df_forecasts, df_model_eval, df_calib, df_decay, df_port = run_multi_horizon_walk_forward_evaluation(
        df_ind_matrix, df_targets, results_dir
    )

    # 4. Generate Reports
    print("\n[Step 4/4] Generating all 10 forecasting reports...")
    build_all_forecasting_reports(df_model_eval, df_calib, df_decay, df_port, reports_dir)

    print("\n" + "=" * 75)
    print(" PHASE 6 MULTI-HORIZON RETURN FORECASTING RUN COMPLETED")
    print(" 10 Reports in:  research/reports/")
    print(" 7 CSV Datasets in: research/results/")
    print(" Master Verdict: research/reports/FINAL_RETURN_FORECAST_VERDICT.md")
    print("=" * 75)

if __name__ == "__main__":
    main()
