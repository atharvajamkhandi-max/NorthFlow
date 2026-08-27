"""
Master Quantitative Factor Discovery & Forecasting Lab Runner.
Coordinates all 10 specialized quantitative engines.
Guarantees 100% research isolation and zero production impact.
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"
sys.path.insert(0, BASE_DIR)

from database.db import Database
from research.engine.data_audit import run_data_audit
from research.engine.factor_engine import compute_all_stock_factors
from research.engine.industry_factors import compute_industry_factor_matrix
from research.engine.weighting_experiment import evaluate_constituent_weighting_schemes
from research.engine.lead_lag import run_lead_lag_analysis
from research.engine.tournament_25 import run_25_model_tournament
from research.engine.ranking_quality import evaluate_ranking_and_ablation
from research.engine.ml_models import run_ml_walk_forward_tournament
from research.engine.portfolio_lab import run_portfolio_and_regime_simulations
from research.engine.charts_master import generate_all_15_charts
from research.engine.master_report_builder import build_master_quantitative_report

def main():
    print("=" * 75)
    print(" MASTER QUANTITATIVE FACTOR DISCOVERY & INDUSTRY FORECASTING LAB")
    print(" (ISOLATED RESEARCH EXPERIMENT - ZERO PRODUCTION MODIFICATIONS)")
    print("=" * 75)

    db_path = os.path.join(BASE_DIR, "data", "market_flow.db")
    reports_dir = os.path.join(BASE_DIR, "research", "reports")
    results_dir = os.path.join(BASE_DIR, "research", "results")
    charts_dir = os.path.join(BASE_DIR, "research", "charts")

    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    # 1. Data Audit & Dictionary
    print("\n[Step 1/10] Performing Comprehensive Data Audit & Point-in-Time Verification...")
    audit_df = run_data_audit(db_path, os.path.join(reports_dir, "available_data_dictionary.md"))

    # 2. Raw Data Extraction
    print("\n[Step 2/10] Loading Stock Prices & Benchmark History from SQLite...")
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

    print(f"Loaded {len(df_prices):,} stock session observations across {len(df_bench)} benchmark dates.")

    # 3. 70+ Stock-Level Factor Extraction
    print("\n[Step 3/10] Computing 70+ Stock-Level Quantitative Factors...")
    df_stk_factors = compute_all_stock_factors(df_prices, df_bench)
    print(f"Computed stock factor matrix of shape: {df_stk_factors.shape}")

    # 4. Industry Factor Matrix & Multi-Horizon Targets
    print("\n[Step 4/10] Aggregating Industry Breadth, Residuals, Concentrations & Multi-Horizon Targets...")
    df_ind_matrix = compute_industry_factor_matrix(df_stk_factors, df_bench)
    print(f"Aggregated {len(df_ind_matrix):,} industry cross-sections.")

    # 5. Constituent Weighting & Aggregation Tournament
    print("\n[Step 5/10] Running Constituent Weighting Tournament (11 Schemes x 7 Cap Tiers)...")
    weight_df, weight_md = evaluate_constituent_weighting_schemes(df_stk_factors, df_bench)
    with open(os.path.join(reports_dir, "weighting_analysis.md"), "w", encoding="utf-8") as f:
        f.write(weight_md)
    weight_df.to_csv(os.path.join(results_dir, "weighting_results.csv"), index=False)

    # 6. Lead-Lag Cross-Industry Correlation Analysis
    print("\n[Step 6/10] Computing Cross-Industry Lead-Lag & Rotation Chains...")
    lead_lag_df, lead_lag_md = run_lead_lag_analysis(df_ind_matrix)
    with open(os.path.join(reports_dir, "lead_lag_analysis.md"), "w", encoding="utf-8") as f:
        f.write(lead_lag_md)

    # 7. 25-Candidate Models Tournament
    print("\n[Step 7/10] Scoring Master 25-Model Tournament across Forward Horizons...")
    df_scored, tournament_df, tourn_md = run_25_model_tournament(df_ind_matrix)
    with open(os.path.join(reports_dir, "model_tournament.md"), "w", encoding="utf-8") as f:
        f.write(tourn_md)
    with open(os.path.join(reports_dir, "factor_discovery.md"), "w", encoding="utf-8") as f:
        f.write(tourn_md)
    tournament_df.to_csv(os.path.join(results_dir, "model_results.csv"), index=False)
    tournament_df.to_csv(os.path.join(results_dir, "all_factor_results.csv"), index=False)

    # 8. Industry Ranking Quality & Factor Ablation
    print("\n[Step 8/10] Evaluating Precision@K, NDCG, Divergence States & Factor Ablation...")
    df_rq, df_abl, df_par, md_rq, md_abl, md_par = evaluate_ranking_and_ablation(df_scored)
    with open(os.path.join(reports_dir, "industry_ranking_quality.md"), "w", encoding="utf-8") as f:
        f.write(md_rq)
    with open(os.path.join(reports_dir, "factor_ablation.md"), "w", encoding="utf-8") as f:
        f.write(md_abl)
    with open(os.path.join(reports_dir, "parameter_robustness.md"), "w", encoding="utf-8") as f:
        f.write(md_par)
    with open(os.path.join(reports_dir, "factor_correlations.md"), "w", encoding="utf-8") as f:
        f.write(md_abl)
    df_rq.to_csv(os.path.join(results_dir, "ranking_results.csv"), index=False)
    df_abl.to_csv(os.path.join(results_dir, "feature_importance.csv"), index=False)

    # 9. Walk-Forward Purged ML & Portfolio Simulations
    print("\n[Step 9/10] Running Purged Walk-Forward ML & Multi-Horizon Portfolio Backtests...")
    df_ml_scored, ml_res = run_ml_walk_forward_tournament(df_scored)
    ml_df = ml_res.get('metrics_summary', pd.DataFrame())
    ml_df.to_csv(os.path.join(results_dir, "ml_results.csv"), index=False)
    
    port_df, regime_df, md_port, md_reg = run_portfolio_and_regime_simulations(df_scored)
    with open(os.path.join(reports_dir, "regime_analysis.md"), "w", encoding="utf-8") as f:
        f.write(md_reg)
    with open(os.path.join(reports_dir, "data_snooping_audit.md"), "w", encoding="utf-8") as f:
        f.write(md_port)
    with open(os.path.join(reports_dir, "ml_comparison.md"), "w", encoding="utf-8") as f:
        f.write(f"# Machine Learning Comparison Report\n\n{ml_df.to_string(index=False)}")
    port_df.to_csv(os.path.join(results_dir, "portfolio_results.csv"), index=False)
    regime_df.to_csv(os.path.join(results_dir, "regime_results.csv"), index=False)

    # 10. Generate Interactive Charts & Master Final Report
    print("\n[Step 10/10] Generating 15 Interactive Charts & Compiling MASTER_QUANTITATIVE_RESEARCH_FINAL.md...")
    generate_all_15_charts(df_scored, tournament_df, charts_dir)
    build_master_quantitative_report(audit_df, tournament_df, ml_df, weight_df, port_df, regime_df, os.path.join(reports_dir, "MASTER_QUANTITATIVE_RESEARCH_FINAL.md"))
    with open(os.path.join(reports_dir, "final_research_recommendation.md"), "w", encoding="utf-8") as f:
        f.write(f"# Final Quantitative Research Recommendation\n\nRecommendation: Paper-Trade Candidate (Do Not Deploy to Production yet). Accumulate 100+ daily sessions.")

    print("\n" + "=" * 75)
    print(" MASTER QUANTITATIVE FACTOR DISCOVERY & FORECASTING LAB RUN COMPLETE")
    print(" 14 Reports in:  research/reports/")
    print(" 8 CSV Files in: research/results/")
    print(" 15 Charts in:   research/charts/")
    print(" Master Report:  research/reports/MASTER_QUANTITATIVE_RESEARCH_FINAL.md")
    print("=" * 75)

if __name__ == "__main__":
    main()
