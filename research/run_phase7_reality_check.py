"""
Phase 7: Adversarial Out-of-Sample Reality Check Master Runner.
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"
sys.path.insert(0, BASE_DIR)

from database.db import Database
from research.engine.phase7_magnitude_and_holdout import run_magnitude_and_holdout_tests
from research.engine.phase7_calibration_and_buckets import run_calibration_and_bucket_tests
from research.engine.phase7_weighting_and_portfolios import run_weighting_and_portfolio_tests
from research.engine.phase7_charts import build_all_phase7_charts
from research.engine.phase7_master_verdict import build_phase7_master_verdicts

def main():
    print("=" * 75)
    print(" PHASE 7: ADVERSARIAL OUT-OF-SAMPLE REALITY CHECK")
    print(" (STRICT RESEARCH ISOLATION - ZERO PRODUCTION MODIFICATIONS)")
    print("=" * 75)

    reports_dir = os.path.join(BASE_DIR, "research", "reports")
    results_dir = os.path.join(BASE_DIR, "research", "results")
    charts_dir = os.path.join(BASE_DIR, "research", "charts")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    # 1. Load Data and Forecasts
    print("\n[Step 1/5] Loading historical prices and walk-forward forecast datasets...")
    db = Database()
    with db.get_connection() as conn:
        df_prices = pd.read_sql_query("""
            SELECT dp.*, s.industry, s.basic_industry 
            FROM daily_prices dp
            JOIN stocks s ON dp.symbol = s.symbol
            WHERE s.active = 1 AND s.basic_industry != 'UNKNOWN'
            ORDER BY dp.symbol ASC, dp.date ASC;
        """, conn)

    df_ret_fwd = pd.read_csv(os.path.join(results_dir, "return_forecasts.csv"))
    df_prob_fwd = pd.read_csv(os.path.join(results_dir, "probability_forecasts.csv"))
    df_quant_fwd = pd.read_csv(os.path.join(results_dir, "quantile_forecasts.csv"))

    # Merge forecasts
    df_forecasts = pd.merge(df_ret_fwd, df_prob_fwd[['date', 'basic_industry', 'model', 'horizon', 'p_pos', 'p_excess']], on=['date', 'basic_industry', 'model', 'horizon'], how='inner')
    df_forecasts = pd.merge(df_forecasts, df_quant_fwd[['date', 'basic_industry', 'model', 'horizon', 'p10', 'p25', 'p50', 'p75', 'p90', 'mfe', 'mae']], on=['date', 'basic_industry', 'model', 'horizon'], how='inner')

    # 2. Magnitude & Holdout Tests
    print("\n[Step 2/5] Running Return Magnitude Reality Check, Shrinkage & Untouched Holdout...")
    df_mag, df_shrink, df_holdout, df_bias = run_magnitude_and_holdout_tests(df_forecasts, reports_dir, results_dir)

    # 3. Calibration, Buckets & Ablation Tests
    print("\n[Step 3/5] Running Decile Conditional Return Buckets, Calibration Audit & 13-Factor Ablation...")
    df_buckets, df_calib_audit, df_ablation = run_calibration_and_bucket_tests(df_forecasts, None, reports_dir, results_dir)

    # 4. Weighting, Dominance & Portfolio Tests
    print("\n[Step 4/5] Running Single-Stock Dominance & Portfolio Simulations across friction tiers...")
    df_conc, df_port_sim = run_weighting_and_portfolio_tests(df_forecasts, df_prices, reports_dir, results_dir)

    # 5. Build Charts and Master Verdicts
    print("\n[Step 5/5] Generating 6 interactive Plotly HTML charts and Master Verdicts...")
    build_all_phase7_charts(df_forecasts, df_buckets, df_calib_audit, None, df_port_sim, charts_dir)
    build_phase7_master_verdicts(reports_dir)

    print("\n" + "=" * 75)
    print(" PHASE 7 ADVERSARIAL REALITY CHECK COMPLETED")
    print(" 12 Reports in:  research/reports/")
    print(" 8 CSV Datasets in: research/results/")
    print(" 6 Interactive Charts in: research/charts/")
    print(" Master Verdict: research/reports/PHASE7_REALITY_CHECK.md")
    print("=" * 75)

if __name__ == "__main__":
    main()
