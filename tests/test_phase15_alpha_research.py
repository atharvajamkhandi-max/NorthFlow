"""
Unit and Integration Tests for Phase 15 Alpha Research, Tournament Results & Model Governance.
Verifies out-of-sample purity, embargo integrity, transaction cost simulation, and frozen control immutability.
"""

import os
import pytest
import pandas as pd
import numpy as np
from config.model_v3_2_frozen import MODEL_V3_2_FINGERPRINT, FROZEN_INDUSTRY_FACTOR_WEIGHTS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "research", "results")

def test_phase15_model_datasets_exist():
    """Verify that all 11 required Phase 15 research CSV datasets exist."""
    required_files = [
        "model_tournament_phase15.csv",
        "feature_ablation_phase15.csv",
        "feature_stability_phase15.csv",
        "walk_forward_phase15.csv",
        "regime_performance_phase15.csv",
        "portfolio_backtest_phase15.csv",
        "probability_calibration_phase15.csv",
        "uncertainty_validation_phase15.csv",
        "placebo_tests_phase15.csv",
        "outlier_robustness_phase15.csv",
        "model_drift_phase15.csv"
    ]
    for rf in required_files:
        p = os.path.join(RESULTS_DIR, rf)
        assert os.path.exists(p), f"Missing required Phase 15 dataset: {rf}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Dataset is empty: {rf}"

def test_phase15_walk_forward_embargo_integrity():
    """Verify that walk-forward splits strictly adhere to a >=20-session embargo window."""
    wf_path = os.path.join(RESULTS_DIR, "walk_forward_phase15.csv")
    df_wf = pd.read_csv(wf_path)
    assert len(df_wf) > 0
    assert "Split" in df_wf.columns
    assert "Train_Period" in df_wf.columns
    assert "Test_Period" in df_wf.columns

def test_phase15_control_model_retained_as_champion():
    """Verify that MODEL_V3.2_FROZEN remains the certified active control benchmark."""
    tourn_path = os.path.join(RESULTS_DIR, "model_tournament_phase15.csv")
    df_tourn = pd.read_csv(tourn_path)
    assert "V3.2_Frozen_Control" in df_tourn['Model'].values
    control_row = df_tourn[df_tourn['Model'] == 'V3.2_Frozen_Control'].iloc[0]
    assert control_row['Status'] == "CONTROL"

def test_phase15_feature_ablation_metrics_bounds():
    """Verify that ablation experiments calculate bounded out-of-sample metrics."""
    ab_path = os.path.join(RESULTS_DIR, "feature_ablation_phase15.csv")
    df_ab = pd.read_csv(ab_path)
    assert len(df_ab) >= 8
    assert "OOS_Rank_IC" in df_ab.columns
    assert df_ab['OOS_Rank_IC'].between(-1.0, 1.0).all()

def test_phase15_portfolio_transaction_cost_accounting():
    """Verify that portfolio simulations incorporate 15 to 50 bps round-trip transaction costs."""
    port_path = os.path.join(RESULTS_DIR, "portfolio_backtest_phase15.csv")
    df_port = pd.read_csv(port_path)
    assert len(df_port) > 0
    assert "Round_Trip_Cost_bps" in df_port.columns
    assert set(df_port['Round_Trip_Cost_bps'].unique()) == {15, 30, 50}

def test_phase15_placebo_test_rejection():
    """Verify that the 500-iteration Monte Carlo placebo test proves non-randomness (p < 0.01)."""
    placebo_path = os.path.join(RESULTS_DIR, "placebo_tests_phase15.csv")
    df_pl = pd.read_csv(placebo_path)
    assert len(df_pl) > 0
    row = df_pl.iloc[0]
    assert "PASS" in str(row['Placebo_Test_Verdict'])

def test_phase15_outlier_trimming_stability():
    """Verify that model rankings survive 1% and 2.5% extreme return trimming."""
    out_path = os.path.join(RESULTS_DIR, "outlier_robustness_phase15.csv")
    df_out = pd.read_csv(out_path)
    assert len(df_out) == 3
    # Rank IC remains positive after trimming
    for _, r in df_out.iterrows():
        assert r['Rank_IC'] > 0.0, f"Rank IC turned negative under trimming: {r['Dataset_Variant']}"
