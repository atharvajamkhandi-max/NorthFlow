"""
Phase 11: Prospective Industry Outperformance Shadow Validation Engine Master Runner.
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
from research.engine.phase11_ledger_and_realization import generate_daily_forecast_snapshots, compute_forward_realizations_and_errors
from research.engine.phase11_validation_analytics import (
    compute_top_k_prospective_performance,
    compute_threshold_calibration_metrics,
    compute_extreme_upside_and_leadership_lifts,
    build_todays_opportunity_board
)
from research.engine.phase11_reports_and_charts import build_phase11_reports_and_charts

def main():
    print("=" * 80)
    print(" PHASE 11: PROSPECTIVE INDUSTRY OUTPERFORMANCE SHADOW VALIDATION ENGINE")
    print(" (FROZEN MODEL VALIDATION LAB - ZERO PRODUCTION MODIFICATIONS)")
    print("=" * 80)

    reports_dir = os.path.join(BASE_DIR, "research", "reports")
    results_dir = os.path.join(BASE_DIR, "research", "results")
    charts_dir = os.path.join(BASE_DIR, "research", "charts")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    # 1. Load Historical Data
    print("\n[Step 1/5] Loading historical prices, benchmark, and active universe from SQLite...")
    db = Database()
    with db.get_connection() as conn:
        df_prices = pd.read_sql_query("""
            SELECT dp.*, s.industry, s.basic_industry 
            FROM daily_prices dp
            JOIN stocks s ON dp.symbol = s.symbol
            WHERE s.active = 1 AND s.basic_industry != 'UNKNOWN'
            ORDER BY dp.symbol ASC, dp.date ASC;
        """, conn)
        df_stocks = pd.read_sql_query("SELECT * FROM stocks WHERE active = 1;", conn)
        df_bench = pd.read_sql_query("SELECT date, close FROM market_benchmark ORDER BY date ASC;", conn)

    # 2. Compute Features & Historical Targets
    print("\n[Step 2/5] Computing feature matrix and multi-horizon realized targets...")
    df_stk_factors = compute_all_stock_factors(df_prices, df_bench)
    df_ind_matrix = compute_industry_factor_matrix(df_stk_factors, df_bench)
    df_targets, _ = compute_forecasting_targets(df_prices, df_bench)

    # 3. Generate Daily Forecast Snapshots with Frozen Model Fingerprint
    print("\n[Step 3/5] Generating Point-in-Time Frozen Forecast Snapshots across all sessions...")
    df_ledger = generate_daily_forecast_snapshots(df_ind_matrix, df_stocks, df_bench)
    df_ledger.to_csv(os.path.join(results_dir, "phase11_daily_forecast_ledger.csv"), index=False)

    # 4. Execute Forward Realization Engine
    print("\n[Step 4/5] Matching Matured Forecasts with Realized Outcomes & Diagnostics...")
    df_realized, df_errors = compute_forward_realizations_and_errors(df_ledger, df_targets)
    df_realized.to_csv(os.path.join(results_dir, "phase11_realized_outcomes.csv"), index=False)
    df_errors.to_csv(os.path.join(results_dir, "phase11_forecast_errors.csv"), index=False)

    # Analytics
    df_top_k = compute_top_k_prospective_performance(df_realized)
    df_top_k.to_csv(os.path.join(results_dir, "phase11_top_k_performance.csv"), index=False)

    df_calib = compute_threshold_calibration_metrics(df_realized)
    df_calib.to_csv(os.path.join(results_dir, "phase11_threshold_calibration.csv"), index=False)

    df_up_lift, df_lead_val = compute_extreme_upside_and_leadership_lifts(df_realized)
    df_up_lift.to_csv(os.path.join(results_dir, "phase11_extreme_upside_validation.csv"), index=False)
    df_lead_val.to_csv(os.path.join(results_dir, "phase11_leadership_validation.csv"), index=False)

    # Individual validation slices
    df_realized[['forecast_date', 'industry', 'current_strength', '20D_realized_ret']].to_csv(os.path.join(results_dir, "phase11_strength_validation.csv"), index=False)
    df_realized[['forecast_date', 'industry', 'forward_opportunity_score', '20D_realized_ret']].to_csv(os.path.join(results_dir, "phase11_opportunity_validation.csv"), index=False)
    df_realized[['forecast_date', 'industry', 'model_consensus', '20D_realized_ret']].to_csv(os.path.join(results_dir, "phase11_consensus_validation.csv"), index=False)
    df_realized[['forecast_date', 'industry', 'reliability', '20D_abs_error']].to_csv(os.path.join(results_dir, "phase11_reliability_validation.csv"), index=False)
    df_realized[['forecast_date', 'industry', 'best_horizon', '20D_realized_excess']].to_csv(os.path.join(results_dir, "phase11_horizon_validation.csv"), index=False)
    df_realized[['forecast_date', 'industry', 'constituent_count', '20D_realized_ret']].to_csv(os.path.join(results_dir, "phase11_stock_bridge_validation.csv"), index=False)
    df_realized[['forecast_date', 'industry', '20D_realized_ret', '20D_realized_excess']].to_csv(os.path.join(results_dir, "phase11_regime_validation.csv"), index=False)

    # Opportunity Board for Latest Session
    dates = sorted(df_ledger['forecast_date'].unique())
    latest_snap = df_ledger[df_ledger['forecast_date'] == dates[-1]].copy()
    board = build_todays_opportunity_board(latest_snap, df_stocks)

    # 5. Generate Master Reports & Interactive Charts
    print("\n[Step 5/5] Generating 14 Markdown Reports and 4 Interactive Plotly Charts...")
    build_phase11_reports_and_charts(
        df_ledger, df_realized, df_errors, df_calib, df_top_k, df_up_lift, df_lead_val, board, reports_dir, charts_dir
    )

    print("\n" + "=" * 80)
    print(" PHASE 11 SHADOW VALIDATION ENGINE COMPLETED SUCCESSFULLY")
    print(" Master Report:     research/reports/PHASE11_PROSPECTIVE_VALIDATION.md")
    print(" All Reports (14):  research/reports/")
    print(" All CSVs (14):     research/results/")
    print(" Interactive Charts: research/charts/phase11_top_k_spread.html")
    print("=" * 80)

if __name__ == "__main__":
    main()
