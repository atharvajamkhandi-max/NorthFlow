"""
Master Executable for Full Quantitative Multi-Model Tournament & Benchmarking.
Orchestrates Phase A through Phase P across all 403 historical sessions.
"""

import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.db import Database
from research.engine.quant_data_auditor import QuantDataAuditor
from research.engine.quant_feature_lab import QuantFeatureLab
from research.engine.quant_regime_and_breadth import QuantRegimeAndBreadth
from research.engine.quant_accumulation_engine import QuantAccumulationEngine
from research.engine.quant_targets_and_splitter import QuantTargetsAndSplitter
from research.engine.quant_multi_model_tournament import QuantMultiModelTournament
from research.engine.quant_calibration_and_uncertainty import QuantCalibrationAndUncertainty
from research.engine.quant_portfolio_simulator import QuantPortfolioSimulator
from research.engine.quant_ablation_and_holdout import QuantAblationAndHoldout
from research.engine.quant_master_reporter_and_charts import QuantMasterReporter

def run_master_research():
    print("=" * 90)
    print(" QUANTITATIVE MULTI-MODEL RESEARCH TOURNAMENT & BENCHMARK VALIDATION ENGINE")
    print(" Model Benchmark: QUANT_MULTI_MODEL_V1 vs EXISTING_DETERMINISTIC_V1")
    print(" 403 Validated NSE Sessions | Walk-Forward Validation | Hard Breadth Filter N >= 5")
    print("=" * 90)
    t0 = time.time()
    db = Database()

    # Phase A & B: Forensic Data Quality Audit
    auditor = QuantDataAuditor(db=db)
    audit_summary, daily_cov = auditor.run_full_audit()

    # Phase D & E: Stock Factor Lab (1.07M rows)
    feat_lab = QuantFeatureLab(db=db)
    df_stock_factors = feat_lab.build_all_features()

    # Market Regime & Breadth Engine
    with db.get_connection() as conn:
        df_bench = db.get_benchmark_prices()
    mkt_df = QuantRegimeAndBreadth.compute_market_and_regimes(df_stock_factors, df_bench)
    df_ind = QuantRegimeAndBreadth.compute_industry_matrix(df_stock_factors, mkt_df)

    # Observable Accumulation / Distribution Pressure Engine
    df_ind_accum = QuantAccumulationEngine.compute_accumulation_distribution(df_ind)

    # Forward Targets & Walk-Forward Splitter with Purge & Embargo
    df_targets = QuantTargetsAndSplitter.compute_forward_targets(df_ind_accum, df_bench)
    all_dates = sorted(df_targets['date'].unique().tolist())
    splits = QuantTargetsAndSplitter.create_walk_forward_splits(all_dates, train_window=140, val_window=40, purge_embargo=20)

    # Phase F & G: Walk-Forward Model Tournament (10 Models)
    df_results, df_preds_all = QuantMultiModelTournament.run_tournament(df_targets, splits)

    # Phase K: Probability Calibration & Uncertainty Engine
    df_calibrated_preds, df_calib_audit = QuantCalibrationAndUncertainty.calibrate_probabilities(df_preds_all)

    # Phase H, I, J: Regime, Breadth Tournament, Feature Ablation
    df_regime = QuantAblationAndHoldout.run_regime_analysis(df_calibrated_preds)
    df_breadth = QuantAblationAndHoldout.run_breadth_tournament(df_targets)
    df_ablation = QuantAblationAndHoldout.run_feature_ablation(df_targets)

    # Phase L: Institutional Portfolio Simulator
    df_ports = QuantPortfolioSimulator.simulate_portfolios(df_calibrated_preds)

    # Phase N: Master Deliverables (15 CSVs, 6 Reports, 15 Charts)
    QuantMasterReporter.generate_all_artifacts(
        audit_summary=audit_summary,
        df_results=df_results,
        df_preds_all=df_calibrated_preds,
        df_calib_audit=df_calib_audit,
        df_regime=df_regime,
        df_breadth=df_breadth,
        df_ablation=df_ablation,
        df_ports=df_ports,
        df_stock_factors=df_stock_factors
    )

    elapsed = time.time() - t0
    print("\n" + "=" * 90)
    print(f" FULL QUANTITATIVE RESEARCH TOURNAMENT COMPLETED SUCCESSFULLY IN {elapsed:.1f}s")
    print("=" * 90)

if __name__ == "__main__":
    run_master_research()
