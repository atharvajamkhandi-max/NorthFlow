import os
import sys
import pandas as pd
import numpy as np

# Set project path
BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"
sys.path.insert(0, BASE_DIR)

from database.db import Database
from research.engine.universe import audit_universe
from research.engine.features import calculate_stock_features
from research.engine.industry_aggregation import compute_industry_aggregations
from research.engine.models import compute_all_candidate_models
from research.engine.ml_models import run_ml_walk_forward_tournament
from research.engine.backtest import evaluate_models_tournament, run_regime_and_cost_analysis
from research.engine.chart_generator import generate_all_research_charts
from research.engine.prediction_logger import log_predictions
from research.engine.report_generator import generate_all_reports

def main():
    print("=" * 70)
    print(" MASTER QUANTITATIVE INDUSTRY RESEARCH, ML & BACKTESTING ENGINE")
    print(" (ISOLATED RESEARCH LAB - ZERO PRODUCTION MODIFICATIONS)")
    print("=" * 70)

    db = Database()

    # Step 1: Universe Coverage Audit
    print("\n[Step 1/8] Auditing Universe Coverage...")
    cov_df = audit_universe(db)
    print(cov_df.to_string(index=False))

    # Step 2: Load Raw Market Data from SQLite
    print("\n[Step 2/8] Loading Price History & Benchmark Data...")
    with db.get_connection() as conn:
        df_prices = pd.read_sql_query("""
            SELECT dp.*, s.industry, s.basic_industry 
            FROM daily_prices dp
            JOIN stocks s ON dp.symbol = s.symbol
            WHERE s.active = 1 AND s.basic_industry != 'UNKNOWN'
            ORDER BY dp.symbol ASC, dp.date ASC;
        """, conn)
        df_bench = pd.read_sql_query("SELECT date, close FROM market_benchmark ORDER BY date ASC;", conn)

    print(f"Loaded {len(df_prices):,} stock session records and {len(df_bench)} benchmark sessions.")

    # Step 3: Stock-Level Feature Engineering
    print("\n[Step 3/8] Computing Comprehensive Stock-Level Features (Momentum, RS, Trend, RSI, Volume, Delivery, Breakouts, Volatility)...")
    df_stk_features = calculate_stock_features(df_prices, df_bench)
    print(f"Computed feature matrix of shape: {df_stk_features.shape}")

    # Step 4: Industry-Level Aggregation, Breadth, Residual Momentum & Dynamic Weighting
    print("\n[Step 4/8] Aggregating Industry Breadth, Residual Momentum & Dynamic Constituent Weighting...")
    df_ind_agg = compute_industry_aggregations(df_stk_features, df_bench)
    print(f"Aggregated {len(df_ind_agg):,} industry cross-sections.")

    # Step 5: Candidate Models Tournament Scoring
    print("\n[Step 5/8] Scoring 15+ Candidate Models & Ensembles...")
    df_scored = compute_all_candidate_models(df_ind_agg)

    # Step 6: Machine Learning Walk-Forward Cross-Validation
    print("\n[Step 6/8] Running Purged Walk-Forward ML Tournament (Logistic, Ridge, ElasticNet, RF, GradientBoosting)...")
    df_scored_ml, ml_res = run_ml_walk_forward_tournament(df_scored)
    ml_metrics_df = ml_res.get('metrics_summary', pd.DataFrame())
    print("\nML Performance Summary:")
    print(ml_metrics_df.to_string(index=False))

    # Step 7: Backtest, Portfolio Simulation & Tournament Evaluation
    print("\n[Step 7/8] Running Portfolio Simulations, Quintile Analysis & Robustness Tests...")
    model_cols = [
        'M1_MultiHorizonMom', 'M2_RiskAdjustedMom', 'M3_ResidualMom',
        'M4_BreadthExpansion', 'M5_DirectionalVolume', 'M6_TrendStack',
        'M7_BreakoutQuality', 'M8_RSI_Momentum', 'M9_MeanReversion',
        'M10_VolAdjustedComposite', 'M_DynamicBottomUp',
        'BASE_5D_Momentum', 'BASE_20D_Momentum', 'BASE_Simple_RS', 'BASE_EqualBreadth',
        'BASE_V2_Research', 'ENSEMBLE_Strength', 'ENSEMBLE_Prediction',
        'ML_Logistic_P5', 'ML_Ridge_Ret5', 'ML_ElasticNet_P5', 'ML_RandomForest_P5', 'ML_GradientBoosting_P5'
    ]
    tourn_res = evaluate_models_tournament(df_scored_ml, model_cols)
    tournament_df = tourn_res.get('tournament_table', pd.DataFrame())
    print("\nCandidate Models Tournament Results:")
    print(tournament_df.to_string(index=False))

    reg_cost_res = run_regime_and_cost_analysis(df_scored_ml, best_model='ENSEMBLE_Prediction')
    cost_df = reg_cost_res.get('cost_table', pd.DataFrame())
    rel_df = reg_cost_res.get('reliability_table', pd.DataFrame())

    # Step 8: Visualizations, Prediction Logging & Comprehensive Reporting
    print("\n[Step 8/8] Generating Interactive Charts, Logging Isolated Predictions & Compiling Research Reports...")
    charts_dir = os.path.join(BASE_DIR, "research", "charts")
    reports_dir = os.path.join(BASE_DIR, "research", "reports")
    results_dir = os.path.join(BASE_DIR, "research", "results")

    generate_all_research_charts(df_scored_ml, tournament_df, charts_dir)
    log_predictions(df_scored_ml)
    generate_all_reports(cov_df, tournament_df, ml_metrics_df, cost_df, rel_df, df_scored_ml, reports_dir, results_dir)

    print("\n" + "=" * 70)
    print(" MASTER QUANTITATIVE RESEARCH EXECUTION COMPLETE")
    print(" All reports saved to: research/reports/")
    print(" All results saved to: research/results/")
    print(" All charts saved to:  research/charts/")
    print(" Isolated predictions: research/data/prediction_log.db")
    print("=" * 70)

if __name__ == "__main__":
    main()
