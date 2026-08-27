"""
Phase 12: Final Industry Outperformance Intelligence, Breadth Filter & Prospective Validation Master Runner.
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
from research.engine.phase12_master_intelligence_engine import run_phase12_intelligence_cycle
from research.engine.phase12_reports_and_charts import build_phase12_reports_and_charts

def main():
    print("=" * 80)
    print(" PHASE 12: FINAL INDUSTRY OUTPERFORMANCE INTELLIGENCE & BREADTH FILTER ENGINE")
    print(" (DETERMINISTIC STATISTICAL LAB - ZERO RUNTIME LLM - ZERO PRODUCTION MODIFICATIONS)")
    print("=" * 80)

    reports_dir = os.path.join(BASE_DIR, "research", "reports")
    results_dir = os.path.join(BASE_DIR, "research", "results")
    charts_dir = os.path.join(BASE_DIR, "research", "charts")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    # 1. Load Data
    print("\n[Step 1/4] Loading active stock universe, historical prices, and benchmark from SQLite...")
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

    # 2. Compute Point-in-Time Features & Forward Targets
    print("\n[Step 2/4] Computing feature matrix and multi-horizon target realizations...")
    df_stk_factors = compute_all_stock_factors(df_prices, df_bench)
    df_ind_matrix = compute_industry_factor_matrix(df_stk_factors, df_bench)
    df_targets, _ = compute_forecasting_targets(df_prices, df_bench)

    # 3. Execute Phase 12 Intelligence Cycle
    print("\n[Step 3/4] Running Breadth Filter (N >= 5), Calibrated Distributions, and Stock Bridge...")
    df_primary, df_research_only, df_dist, df_stock_bridge = run_phase12_intelligence_cycle(
        df_ind_matrix, df_stk_factors, df_stocks, df_bench, df_targets, results_dir
    )

    # 4. Generate Master Report & Plotly Visualizations
    print("\n[Step 4/4] Generating Phase 12 Master Report and 4 Interactive Plotly Charts...")
    build_phase12_reports_and_charts(
        df_primary, df_research_only, df_dist, df_stock_bridge, reports_dir, charts_dir
    )

    print("\n" + "=" * 80)
    print(" PHASE 12 MASTER INTELLIGENCE ENGINE COMPLETED SUCCESSFULLY")
    print(f" Primary Eligible Industries (N >= 5): {len(df_primary)}")
    print(f" Research-Only Industries (N < 5):     {len(df_research_only)}")
    print(f" Total Industries Evaluated:           {len(df_primary) + len(df_research_only)}")
    print(" Master Report:     research/reports/PHASE12_FINAL_INDUSTRY_INTELLIGENCE.md")
    print(" Interactive Charts: research/charts/phase12_primary_opportunities.html")
    print("=" * 80)

if __name__ == "__main__":
    main()
