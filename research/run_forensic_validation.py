"""
Master Forensic Validation Lab Runner.
Executes all 5 forensic validation engines in isolated research mode.
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
from research.engine.tournament_25 import run_25_model_tournament

from research.engine.forensic_reconciliation import run_result_reconciliation
from research.engine.forensic_sample_audit import run_session_audit
from research.engine.forensic_overlap_and_bootstrap import run_overlap_and_bootstrap_analysis
from research.engine.forensic_plateau_and_weighting import run_plateau_and_weighting_forensics
from research.engine.forensic_incremental_and_placebo import run_incremental_and_placebo_forensics
from research.engine.forensic_final_verdict import build_final_forensic_verdict

def main():
    print("=" * 75)
    print(" MASTER FORENSIC VALIDATION & ADVERSARIAL AUDIT LAB")
    print(" (STRICT RESEARCH ISOLATION - ZERO PRODUCTION MODIFICATIONS)")
    print("=" * 75)

    db_path = os.path.join(BASE_DIR, "data", "market_flow.db")
    reports_dir = os.path.join(BASE_DIR, "research", "reports")
    results_dir = os.path.join(BASE_DIR, "research", "results")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # 1. Result Reconciliation
    print("\n[Forensic Step 1/6] Reconciling all previous outputs and explaining discrepancies...")
    run_result_reconciliation(reports_dir)

    # 2. Session & Independent Period Audit
    print("\n[Forensic Step 2/6] Auditing exact 37 trading dates and non-overlapping periods...")
    run_session_audit(db_path, results_dir)

    # 3. Load Raw Data and Compute Matrices
    print("\n[Forensic Step 3/6] Extracting data and computing industry feature matrix...")
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

    df_stk_factors = compute_all_stock_factors(df_prices, df_bench)
    df_ind_matrix = compute_industry_factor_matrix(df_stk_factors, df_bench)
    df_scored, _, _ = run_25_model_tournament(df_ind_matrix)

    # 4. Overlapping Bias & 5,000-Resample Block Bootstrap
    print("\n[Forensic Step 4/6] Running Overlapping vs Non-Overlapping & 5,000 Block Bootstrap...")
    run_overlap_and_bootstrap_analysis(df_scored, reports_dir, results_dir)

    # 5. Parameter Plateau, Permutations, Small-N & Liquidity Tests
    print("\n[Forensic Step 5/6] Testing Parameter Plateaus, Shuffling Permutations & Liquidity Buckets...")
    run_plateau_and_weighting_forensics(df_stk_factors, df_scored, df_bench, reports_dir, results_dir)

    # 6. Incremental Factors, ML Comparison, Placebo & FDR
    print("\n[Forensic Step 6/6] Running Incremental Step-Up, Placebos, ML Comparison & FDR...")
    run_incremental_and_placebo_forensics(df_scored, reports_dir, results_dir)

    # 7. Final Verdict Compilation
    print("\n[Final Verdict] Compiling FINAL_RESEARCH_VERDICT.md & Forensic Reports...")
    build_final_forensic_verdict(reports_dir, results_dir)

    print("\n" + "=" * 75)
    print(" MASTER FORENSIC VALIDATION RUN COMPLETED SUCCESSFULLY")
    print(" Master Verdict: research/reports/FINAL_RESEARCH_VERDICT.md")
    print("=" * 75)

if __name__ == "__main__":
    main()
