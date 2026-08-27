"""
Master Executable for Phase V2 Institutional Quantitative Research Engine.
Coordinates end-to-end execution of V2 Factor Lab, Residualized Targets, Accumulation Engine,
Formula Discovery, 15-Model Tournament, Hierarchical Expected Returns, Portfolio Neutrality,
Block Bootstrap, and Master Reporting Suite across all 403 historical sessions.
"""

import os
import sys
import time
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from database.db import Database
from research.engine.quant_data_auditor import QuantDataAuditor
from research.engine.quant_targets_and_splitter import QuantTargetsAndSplitter
from research.engine.quant_ablation_and_holdout import QuantAblationAndHoldout
from research.v2.engine.v2_data_and_factors import V2FactorLab
from research.v2.engine.v2_hierarchy_and_residuals import V2HierarchyAndResiduals
from research.v2.engine.v2_accumulation_engine import V2AccumulationEngine
from research.v2.engine.v2_formula_discovery import V2FormulaDiscoveryEngine
from research.v2.engine.v2_multi_model_tournament import V2MultiModelTournament
from research.v2.engine.v2_hierarchical_expected_returns import V2HierarchicalExpectedReturns
from research.v2.engine.v2_portfolio_and_neutrality import V2PortfolioSimulator
from research.v2.engine.v2_bootstrap_and_drift import V2BootstrapAndDrift
from research.v2.engine.v2_master_reporter import V2MasterReporter

def run_v2_quant_research_master():
    print("=" * 100)
    print(" PHASE V2: INSTITUTIONAL QUANTITATIVE EQUITY & INDUSTRY ALPHA RESEARCH SYSTEM")
    print(" Control / Champion: Existing_Deterministic_V1 | 403 Validated NSE Sessions | Namespace: research/v2/")
    print("=" * 100)
    t0 = time.time()
    db = Database()

    # 1. Forensic Data Quality Audit
    auditor = QuantDataAuditor(db=db)
    audit_summary, daily_cov = auditor.run_full_audit()

    # 2. V2 Factor Lab (1.07M rows)
    feat_lab = V2FactorLab(db=db)
    df_stock_factors = feat_lab.build_all_factors()

    # 3. V2 Hierarchy & Residuals Engine
    df_bench = db.get_benchmark_prices()
    mkt_df, sec_df, ind_df = V2HierarchyAndResiduals.compute_hierarchical_aggregates(df_stock_factors, df_bench)

    # 4. V2 Accumulation / Distribution Engine (5 States)
    ind_df_accum = V2AccumulationEngine.compute_accumulation_states(ind_df)

    # 5. Forward Targets & Walk-Forward Splitter with 20D Purge & Embargo
    df_targets = QuantTargetsAndSplitter.compute_forward_targets(ind_df_accum, df_bench)
    all_dates = sorted(df_targets['date'].unique().tolist())
    splits = QuantTargetsAndSplitter.create_walk_forward_splits(all_dates, train_window=140, val_window=40, purge_embargo=20)

    # 6. Controlled Formula Discovery with Complexity Penalties
    df_formula_results, df_formula_preds = V2FormulaDiscoveryEngine.run_formula_discovery(df_targets)

    # 7. V2 15-Model Master Tournament
    df_results, df_preds_all = V2MultiModelTournament.run_tournament_v2(df_targets, splits)

    # 8. Hierarchical Expected Return Decomposition & Tail Calibration
    df_full_ind_meta = df_targets.merge(df_preds_all[['date', 'basic_industry', 'pred_champion', 'pred_v2_ensemble', 'ensemble_dispersion']], on=['date', 'basic_industry'], how='inner')
    df_full_ind_meta['pred_existing_v1'] = df_full_ind_meta['pred_champion']
    df_full_ind_meta['pred_ensemble'] = df_full_ind_meta['pred_v2_ensemble']
    
    df_multi_horizon, df_calib_audit = V2HierarchicalExpectedReturns.compute_hierarchical_forecasts(df_full_ind_meta)
    df_multi_horizon['pred_existing_v1'] = df_multi_horizon['pred_champion']
    df_multi_horizon['pred_ensemble'] = df_multi_horizon['pred_v2_ensemble']

    # 9. Stationary Block Bootstrap & Drift Monitoring
    df_boot = V2BootstrapAndDrift.run_block_bootstrap(df_multi_horizon)
    df_drift = V2BootstrapAndDrift.monitor_model_drift_v2(df_multi_horizon)
    leakage_audit = V2BootstrapAndDrift.run_anti_leakage_audit()

    # 10. Regime Robustness, Breadth Tournament, Feature Ablation
    df_regime = QuantAblationAndHoldout.run_regime_analysis(df_multi_horizon)
    df_breadth = QuantAblationAndHoldout.run_breadth_tournament(df_targets)
    df_ablation = QuantAblationAndHoldout.run_feature_ablation(df_targets)

    # 11. Simulated Institutional Portfolios & Neutrality Tests with Costs
    df_ports = V2PortfolioSimulator.simulate_portfolios_v2(df_multi_horizon)

    # 12. Master Reporting Suite (13 Reports, 19 CSVs, 17 Charts)
    V2MasterReporter.generate_v2_artifacts(
        audit_summary=audit_summary,
        df_results=df_results,
        df_formula_results=df_formula_results,
        df_preds_all=df_multi_horizon,
        df_calib_audit=df_calib_audit,
        df_regime=df_regime,
        df_breadth=df_breadth,
        df_ablation=df_ablation,
        df_ports=df_ports,
        df_drift=df_drift,
        df_boot=df_boot,
        df_stock_factors=df_stock_factors,
        leakage_audit=leakage_audit
    )

    elapsed = time.time() - t0
    print("\n" + "=" * 100)
    print(f" PHASE V2 INSTITUTIONAL RESEARCH SUITE COMPLETED SUCCESSFULLY IN {elapsed:.1f}s")
    print("=" * 100)

if __name__ == "__main__":
    run_v2_quant_research_master()
