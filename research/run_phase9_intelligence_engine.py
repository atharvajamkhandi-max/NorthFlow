"""
Phase 9: Industry Outperformance & Forward Return Intelligence Engine Master Runner.
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
from research.engine.phase9_outperformance_engine import compute_phase9_intelligence
from research.engine.phase9_prospective_log import update_prospective_shadow_log
from research.engine.phase9_reports_and_charts import build_phase9_reports_and_charts

def main():
    print("=" * 80)
    print(" PHASE 9: INDUSTRY OUTPERFORMANCE & FORWARD RETURN INTELLIGENCE ENGINE")
    print(" (OPPORTUNITY DETECTION LAB - ZERO PRODUCTION MODIFICATIONS)")
    print("=" * 80)

    reports_dir = os.path.join(BASE_DIR, "research", "reports")
    results_dir = os.path.join(BASE_DIR, "research", "results")
    charts_dir = os.path.join(BASE_DIR, "research", "charts")
    data_dir = os.path.join(BASE_DIR, "research", "data")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    # 1. Load Data
    print("\n[Step 1/5] Loading historical prices, benchmark, and stock universe...")
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
    print("\n[Step 2/5] Computing feature matrix, forward excess returns, and historical targets...")
    df_stk_factors = compute_all_stock_factors(df_prices, df_bench)
    df_ind_matrix = compute_industry_factor_matrix(df_stk_factors, df_bench)
    df_targets, _ = compute_forecasting_targets(df_prices, df_bench)

    # 3. Execute Phase 9 Outperformance Intelligence Engine
    print("\n[Step 3/5] Computing Relative Outperformance, Threshold Probabilities & Analogs...")
    df_opp, df_high_conv, df_probs, df_analogs, df_lead_acc, df_horizons = compute_phase9_intelligence(
        df_ind_matrix, df_targets, df_stocks, None, results_dir
    )

    # 4. Update Prospective Shadow Forecast Log
    print("\n[Step 4/5] Logging point-in-time predictions into Prospective Shadow Ledger...")
    update_prospective_shadow_log(df_opp, data_dir, results_dir)

    # 5. Generate Master Reports & Interactive Charts
    print("\n[Step 5/5] Generating Phase 9 Master Report and 4 Plotly HTML Charts...")
    build_phase9_reports_and_charts(df_opp, df_high_conv, df_probs, df_analogs, reports_dir, charts_dir)

    print("\n" + "=" * 80)
    print(" PHASE 9 INDUSTRY OUTPERFORMANCE ENGINE COMPLETED SUCCESSFULLY")
    print(" Master Report:     research/reports/PHASE9_INDUSTRY_OUTPERFORMANCE_ENGINE.md")
    print(" Top Opportunities: research/results/phase9_industry_opportunities.csv")
    print(" High Conviction:   research/results/phase9_highest_conviction.csv")
    print(" Interactive Charts: research/charts/phase9_opportunity_vs_strength.html")
    print("=" * 80)

if __name__ == "__main__":
    main()
