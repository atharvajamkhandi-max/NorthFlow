"""
Master Executable for Institutional Quantitative Research Tournament.
Coordinates end-to-end execution of Phases A through P across all 403 historical sessions.
"""

import os
import sys
import time
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.db import Database
from research.engine.quant_data_auditor import QuantDataAuditor
from research.engine.quant_feature_lab import QuantFeatureLab
from research.engine.quant_regime_and_breadth import QuantRegimeAndBreadth
from research.engine.quant_accumulation_engine import QuantAccumulationEngine
from research.engine.quant_targets_and_splitter import QuantTargetsAndSplitter
from research.engine.quant_ml_diagnosis import QuantMLDiagnosisEngine
from research.engine.quant_formula_tournament import QuantFormulaTournament
from research.engine.quant_multi_model_tournament import QuantMultiModelTournament
from research.engine.quant_multi_horizon_engine import QuantMultiHorizonEngine
from research.engine.quant_calibration_and_uncertainty import QuantCalibrationAndUncertainty
from research.engine.quant_model_drift_monitor import QuantModelDriftMonitor
from research.engine.quant_portfolio_simulator import QuantPortfolioSimulator
from research.engine.quant_ablation_and_holdout import QuantAblationAndHoldout
from research.engine.quant_master_reporting_suite import QuantMasterReportingSuite

def run_master_institutional_research():
    print("=" * 95)
    print(" MASTER INSTITUTIONAL QUANTITATIVE RESEARCH & FORMULA TOURNAMENT ENGINE")
    print(" Champion: Existing_Deterministic_V1 | 403 Validated NSE Sessions | Breadth N >= 5")
    print("=" * 95)
    t0 = time.time()
    db = Database()

    # 1. Forensic Data Quality Audit
    auditor = QuantDataAuditor(db=db)
    audit_summary, daily_cov = auditor.run_full_audit()

    # 2. Stock Factor Lab (1.07M rows)
    feat_lab = QuantFeatureLab(db=db)
    df_stock_factors = feat_lab.build_all_features()

    # 3. Market Regime & Breadth Engine
    df_bench = db.get_benchmark_prices()
    mkt_df = QuantRegimeAndBreadth.compute_market_and_regimes(df_stock_factors, df_bench)
    df_ind = QuantRegimeAndBreadth.compute_industry_matrix(df_stock_factors, mkt_df)

    # 4. Observable Accumulation / Distribution Pressure Engine
    df_ind_accum = QuantAccumulationEngine.compute_accumulation_distribution(df_ind)

    # 5. Forward Targets & Walk-Forward Splitter with Purge & Embargo
    df_targets = QuantTargetsAndSplitter.compute_forward_targets(df_ind_accum, df_bench)
    all_dates = sorted(df_targets['date'].unique().tolist())
    splits = QuantTargetsAndSplitter.create_walk_forward_splits(all_dates, train_window=140, val_window=40, purge_embargo=20)

    # 6. Walk-Forward Model Tournament (10 Models)
    df_results, df_preds_all = QuantMultiModelTournament.run_tournament(df_targets, splits)

    # 7. ML Failure Diagnostic Analysis
    diagnosis_report = QuantMLDiagnosisEngine.run_failure_diagnosis(df_preds_all, df_results)

    # 8. Mathematical Formula Tournament (8 Candidate Formulas vs Champion Baseline)
    df_formula_results, df_formula_preds = QuantFormulaTournament.run_formula_tournament(df_targets)

    # 9. Multi-Horizon Probabilistic Return Engine (1D, 5D, 20D, 60D + 4 Questions Q1-Q4)
    # Merge predictions with full targets metadata
    df_full_ind_meta = df_targets.merge(df_preds_all[['date', 'basic_industry', 'pred_existing_v1', 'pred_ensemble', 'ensemble_dispersion']], on=['date', 'basic_industry'], how='inner')
    df_multi_horizon = QuantMultiHorizonEngine.compute_multi_horizon_forecasts(df_full_ind_meta)

    # 10. Probability Calibration & Prediction Intervals
    df_calibrated_preds, df_calib_audit = QuantCalibrationAndUncertainty.calibrate_probabilities(df_multi_horizon)

    # 11. Model Drift & Stability Monitoring (HEALTHY, WATCH, DEGRADING, FAILED)
    df_drift = QuantModelDriftMonitor.compute_model_drift(df_calibrated_preds)

    # 12. Regime Robustness, Breadth Tournament, Feature Ablation
    df_regime = QuantAblationAndHoldout.run_regime_analysis(df_calibrated_preds)
    df_breadth = QuantAblationAndHoldout.run_breadth_tournament(df_targets)
    df_ablation = QuantAblationAndHoldout.run_feature_ablation(df_targets)

    # 13. Institutional Portfolio Simulator with Transaction Costs
    df_ports = QuantPortfolioSimulator.simulate_portfolios(df_calibrated_preds)

    # 14. Master Reporting Suite (9 Reports, 16 CSVs, 15 Charts)
    QuantMasterReportingSuite.generate_all_artifacts(
        audit_summary=audit_summary,
        df_results=df_results,
        df_formula_results=df_formula_results,
        df_preds_all=df_calibrated_preds,
        df_calib_audit=df_calib_audit,
        df_regime=df_regime,
        df_breadth=df_breadth,
        df_ablation=df_ablation,
        df_ports=df_ports,
        df_drift=df_drift,
        df_stock_factors=df_stock_factors,
        diagnosis_report=diagnosis_report
    )

    elapsed = time.time() - t0
    print("\n" + "=" * 95)
    print(f" FULL INSTITUTIONAL RESEARCH SUITE COMPLETED SUCCESSFULLY IN {elapsed:.1f}s")
    print("=" * 95)

if __name__ == "__main__":
    run_master_institutional_research()
