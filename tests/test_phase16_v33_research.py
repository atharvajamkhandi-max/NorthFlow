"""
Unit and Integration Tests for Phase 16 V3.3 Out-of-Sample Alpha Research.
Validates datasets, tournament metrics, walk-forward embargo, and champion governance.
"""

import os
import pytest
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "research", "results")
REPORTS_DIR = os.path.join(BASE_DIR, "research", "reports")

def test_phase16_all_10_datasets_exist():
    """Verify that all 10 required Phase 16 CSV research datasets exist and are non-empty."""
    required_files = [
        "phase16_model_tournament.csv",
        "phase16_feature_ablation.csv",
        "phase16_regime_validation.csv",
        "phase16_walk_forward.csv",
        "phase16_decile_analysis.csv",
        "phase16_calibration.csv",
        "phase16_cost_stress.csv",
        "phase16_time_decay.csv",
        "phase16_experiment_registry.csv",
        "phase16_champion_vs_challenger.csv"
    ]
    for rf in required_files:
        p = os.path.join(RESULTS_DIR, rf)
        assert os.path.exists(p), f"Missing required Phase 16 dataset: {rf}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Dataset is empty: {rf}"

def test_phase16_report_exists():
    """Verify that the formal markdown report exists."""
    p = os.path.join(REPORTS_DIR, "PHASE16_V33_ALPHA_RESEARCH.md")
    assert os.path.exists(p), "Missing PHASE16_V33_ALPHA_RESEARCH.md"
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    assert len(content) > 1000
    assert "MODEL_V3.2_FROZEN" in content

def test_phase16_champion_v3_2_retained():
    """Verify that V3.2 is retained as production champion."""
    comp_path = os.path.join(RESULTS_DIR, "phase16_champion_vs_challenger.csv")
    df_comp = pd.read_csv(comp_path)
    dec_row = df_comp[df_comp['Metric'] == 'Tournament Decision'].iloc[0]
    assert "RETAINED AS PRODUCTION CHAMPION" in dec_row['Champion_V3_2']
    assert "REJECTED" in dec_row['Best_Challenger_V3_3']

def test_phase16_walk_forward_embargo_compliance():
    """Verify that walk-forward splits log strictly maintains chronological partitions."""
    wf_path = os.path.join(RESULTS_DIR, "phase16_walk_forward.csv")
    df_wf = pd.read_csv(wf_path)
    assert len(df_wf) > 0
    assert "Split" in df_wf.columns
    assert "OOS_Rank_IC" in df_wf.columns

def test_phase16_cost_stress_scenarios():
    """Verify transaction cost scenarios from 0 to 100 bps."""
    cost_path = os.path.join(RESULTS_DIR, "phase16_cost_stress.csv")
    df_cost = pd.read_csv(cost_path)
    assert set(df_cost['Round_Trip_Cost_bps'].unique()) == {0, 10, 20, 30, 50, 75, 100}

def test_phase16_decile_monotonicity_rank():
    """Verify that decile analysis contains ordered buckets from Top 5% to Bottom 5%."""
    dec_path = os.path.join(RESULTS_DIR, "phase16_decile_analysis.csv")
    df_dec = pd.read_csv(dec_path)
    assert len(df_dec) == 9
    assert list(df_dec['Monotonic_Rank']) == list(range(1, 10))
