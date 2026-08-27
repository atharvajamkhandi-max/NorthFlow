"""
Phase 13A: 365-Trading-Session Historical Expansion & Out-of-Sample Validation Master Runner.
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"
sys.path.insert(0, BASE_DIR)

from database.db import Database
from pipeline.historical_365d_expansion import Historical365dExpansionEngine
from pipeline.historical_data_auditor import run_historical_data_quality_audit
from research.engine.phase13a_rebuild_engine import rebuild_full_history_features_and_targets
from research.engine.phase13a_tournament_and_validation import run_walk_forward_tournament
from research.engine.phase13a_reports_and_charts import build_phase13a_reports_and_charts
from research.engine.phase12_master_intelligence_engine import run_phase12_intelligence_cycle

def main():
    print("=" * 80)
    print(" PHASE 13A: 365-TRADING-SESSION HISTORICAL DATA EXPANSION & VALIDATION ENGINE")
    print(" (NSELib Acquisition + Walk-Forward Validation + Hard Breadth Filter N >= 5)")
    print("=" * 80)

    reports_dir = os.path.join(BASE_DIR, "research", "reports")
    results_dir = os.path.join(BASE_DIR, "research", "results")
    charts_dir = os.path.join(BASE_DIR, "research", "charts")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    db = Database()

    # 1. Historical Data Expansion Engine & Backup
    print("\n[Step 1/5] Backing up 37-session database and preparing historical expansion...")
    expansion_engine = Historical365dExpansionEngine(target_sessions=365)
    expansion_engine.backup_existing_database()

    # 2. Run Data Quality Audit
    print("\n[Step 2/5] Performing Forensic Data Quality Audit...")
    audit_summary = run_historical_data_quality_audit(db, reports_dir, results_dir, expected_sessions=365)
    df_audit = pd.read_csv(os.path.join(results_dir, "historical_data_quality.csv"))

    # 3. Rebuild Deterministic Point-in-Time Features & Targets
    print("\n[Step 3/5] Rebuilding Deterministic Features and Forward Targets across Full History...")
    df_prices, df_stocks, df_bench, df_stk_factors, df_ind_matrix, df_targets = rebuild_full_history_features_and_targets(db)

    # 4. Walk-Forward Tournament, Breadth Comparisons, Regime Analysis
    print("\n[Step 4/5] Running Walk-Forward Tournament & Breadth Threshold Audit (N >= 3, 5, 7, 10, 15)...")
    df_breadth, df_models, df_regime, df_tail = run_walk_forward_tournament(
        df_ind_matrix, df_targets, df_stocks, results_dir
    )

    # Execute Phase 12 intelligence cycle on the latest expanded state
    df_primary, df_research_only, df_dist, df_stock_bridge = run_phase12_intelligence_cycle(
        df_ind_matrix, df_stk_factors, df_stocks, df_bench, df_targets, results_dir
    )

    # 5. Generate Master Reports & Interactive Plotly Charts
    print("\n[Step 5/5] Generating Master Expansion Report and Interactive Charts...")
    build_phase13a_reports_and_charts(
        df_audit, df_breadth, df_models, df_regime, df_tail, reports_dir, charts_dir
    )

    print("\n" + "=" * 80)
    print(" PHASE 13A HISTORICAL EXPANSION & VALIDATION COMPLETED SUCCESSFULLY")
    print(f" Total Sessions Evaluated:         {audit_summary['valid_sessions']}")
    print(f" Primary Eligible Industries (N>=5): {len(df_primary)}")
    print(f" Research-Only Industries (N<5):   {len(df_research_only)}")
    print(" Master Report:     research/reports/PHASE13_365_DAY_HISTORICAL_EXPANSION.md")
    print(" Quality Report:    research/reports/historical_data_quality_report.md")
    print(" Interactive Chart: research/charts/phase13a_breadth_threshold_comparison.html")
    print("=" * 80)

if __name__ == "__main__":
    main()
