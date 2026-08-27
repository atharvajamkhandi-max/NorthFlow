"""
Phase 8: Final Quantitative Forecasting Engine & Master Runner.
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
from research.engine.phase8_universe_and_audit import audit_point_in_time_and_universe
from research.engine.phase8_forecasting_engines import build_phase8_forecast_engines
from research.engine.phase8_reports_and_charts import build_phase8_reports_and_charts

def main():
    print("=" * 80)
    print(" PHASE 8: FINAL QUANTITATIVE FORECASTING ENGINE & OUT-OF-SAMPLE VALIDATION")
    print(" (STRICT RESEARCH ISOLATION - ZERO PRODUCTION MODIFICATIONS)")
    print("=" * 80)

    reports_dir = os.path.join(BASE_DIR, "research", "reports")
    results_dir = os.path.join(BASE_DIR, "research", "results")
    charts_dir = os.path.join(BASE_DIR, "research", "charts")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    # 1. Load Data
    print("\n[Step 1/5] Loading historical prices, benchmark, and stock universe from SQLite...")
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

    # 2. Point-in-Time & Universe Audit
    print("\n[Step 2/5] Running Point-in-Time Audit & Complete 135-Industry Universe Check...")
    df_universe = audit_point_in_time_and_universe(df_prices, df_stocks, df_bench, reports_dir)

    # 3. Factor & Target Computation
    print("\n[Step 3/5] Computing feature matrix and forward multi-horizon targets...")
    df_stk_factors = compute_all_stock_factors(df_prices, df_bench)
    df_ind_matrix = compute_industry_factor_matrix(df_stk_factors, df_bench)
    df_targets, _ = compute_forecasting_targets(df_prices, df_bench)

    # 4. Master Forecasting Engines Execution & 8 CSV Export
    print("\n[Step 4/5] Executing 3-Tier Forecasting Engines (Current Strength, Return Forecasts, Quantiles)...")
    df_forecast_snap, df_prob_out, df_quant_out, df_curr_out, df_scorecard, df_stability, df_contrib, df_port_out = build_phase8_forecast_engines(
        df_ind_matrix, df_targets, df_stocks, df_universe, results_dir
    )

    # 5. Build Reports & Charts
    print("\n[Step 5/5] Generating 11 Markdown Reports and 7 Interactive Plotly Charts...")
    build_phase8_reports_and_charts(
        df_forecast_snap, df_scorecard, df_stability, df_contrib, df_port_out, reports_dir, charts_dir
    )

    print("\n" + "=" * 80)
    print(" PHASE 8 MASTER RUN COMPLETED SUCCESSFULLY")
    print(" 11 Markdown Reports in: research/reports/")
    print(" 8 CSV Datasets in:      research/results/")
    print(" 7 Plotly Charts in:     research/charts/")
    print(" Master Verdict:         research/reports/PHASE8_FINAL_ENGINE.md")
    print(" Reality Report:         research/reports/final_research_verdict.md")
    print("=" * 80)

if __name__ == "__main__":
    main()
