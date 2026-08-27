"""
Unit and Integration Test Suite for Phase 17:
2020-2026 Full-History Alpha Enhancement & Early-Warning Validation.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "research" / "results"
REPORTS_DIR = BASE_DIR / "research" / "reports"

def test_phase17_all_12_datasets_exist():
    """Verify all 12 required Phase 17 CSV datasets exist and are non-empty."""
    required_files = [
        "phase17_feature_validation.csv",
        "phase17_incremental_model_comparison.csv",
        "phase17_yearly_results.csv",
        "phase17_regime_results.csv",
        "phase17_industry_rotation.csv",
        "phase17_stock_selection.csv",
        "phase17_accumulation_distribution.csv",
        "phase17_probability_calibration.csv",
        "phase17_placebo.csv",
        "phase17_transaction_costs.csv",
        "phase17_feature_redundancy.csv",
        "phase17_2026_holdout.csv"
    ]
    for rf in required_files:
        p = RESULTS_DIR / rf
        assert p.exists(), f"Missing required Phase 17 dataset: {rf}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Dataset is empty: {rf}"

def test_phase17_report_exists():
    """Verify Phase 17 formal report exists and is populated."""
    p = REPORTS_DIR / "PHASE17_2020_2026_EARLY_WARNING_RESEARCH.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert len(content) > 1000
    assert "MODEL_V3.2_FROZEN" in content

def test_phase17_2026_holdout_integrity():
    """Verify 2026 untouched holdout results."""
    p = RESULTS_DIR / "phase17_2026_holdout.csv"
    df = pd.read_csv(p)
    assert len(df) > 0
    assert "V3_2_Control_Rank_IC" in df.columns
    assert "V3_2_Plus_EW_Rank_IC" in df.columns
    assert float(df['V3_2_Control_Rank_IC'].iloc[0]) > 0.0

def test_phase17_quadrant_matrix_partition():
    """Verify 4-quadrant transition matrix partition."""
    p = RESULTS_DIR / "phase17_regime_results.csv"
    df = pd.read_csv(p)
    assert len(df) >= 4
    assert "quadrant" in df.columns
    assert "Avg_20D_Return" in df.columns

def test_phase17_cost_stress_scenarios():
    """Verify transaction cost stress testing from 0 to 100 bps."""
    p = RESULTS_DIR / "phase17_transaction_costs.csv"
    df = pd.read_csv(p)
    assert set(df['Round_Trip_Cost_bps'].unique()) == {0, 15, 30, 50, 75, 100}

def test_phase17_placebo_test_randomization():
    """Verify placebo randomization test completed."""
    p = RESULTS_DIR / "phase17_placebo.csv"
    df = pd.read_csv(p)
    assert len(df) > 0
    assert "Empirical_p_value" in df.columns
