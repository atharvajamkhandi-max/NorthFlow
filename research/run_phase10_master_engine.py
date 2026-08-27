"""
Phase 10: Advanced Industry Alpha, Return Magnitude & High-Upside Discovery Engine Master Runner.
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
from research.engine.phase10_master_engine import run_phase10_master_alpha_engine
from research.engine.phase10_reports_and_charts import build_phase10_reports_and_charts

def main():
    print("=" * 80)
    print(" PHASE 10: ADVANCED INDUSTRY ALPHA, RETURN MAGNITUDE & HIGH-UPSIDE DISCOVERY ENGINE")
    print(" (OPPORTUNITY INTELLIGENCE LAB - ZERO PRODUCTION MODIFICATIONS)")
    print("=" * 80)

    reports_dir = os.path.join(BASE_DIR, "research", "reports")
    results_dir = os.path.join(BASE_DIR, "research", "results")
    charts_dir = os.path.join(BASE_DIR, "research", "charts")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    # 1. Load Data
    print("\n[Step 1/4] Loading historical prices, benchmark, and active stock universe...")
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

    # 2. Compute Features & Multi-Horizon Targets
    print("\n[Step 2/4] Computing feature matrix, forward returns, and historical targets...")
    df_stk_factors = compute_all_stock_factors(df_prices, df_bench)
    df_ind_matrix = compute_industry_factor_matrix(df_stk_factors, df_bench)
    df_targets, _ = compute_forecasting_targets(df_prices, df_bench)

    # 3. Execute Phase 10 Master Alpha Engine
    print("\n[Step 3/4] Running Non-Gaussian Distributions, Tail Thresholds, Extreme Upside & Consensus...")
    dfs = run_phase10_master_alpha_engine(
        df_ind_matrix, df_targets, df_stocks, df_bench, df_stk_factors, results_dir
    )

    # 4. Generate Master Reports & Interactive Charts
    print("\n[Step 4/4] Generating 13 Markdown Reports and 4 Interactive Plotly Charts...")
    build_phase10_reports_and_charts(dfs, reports_dir, charts_dir)

    print("\n" + "=" * 80)
    print(" PHASE 10 MASTER ENGINE COMPLETED SUCCESSFULLY")
    print(" Master Report:     research/reports/PHASE10_ADVANCED_INDUSTRY_ALPHA.md")
    print(" All Reports (13):  research/reports/")
    print(" All CSVs (11):     research/results/")
    print(" Interactive Charts: research/charts/phase10_top20_opportunity_cards.html")
    print("=" * 80)

if __name__ == "__main__":
    main()
