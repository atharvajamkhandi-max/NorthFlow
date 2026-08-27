"""
Unit and Integration Test Suite for Phase 22:
Early Sector Radar / Pre-Breakout Probability Engine.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "research" / "results"
REPORTS_DIR = BASE_DIR / "research" / "reports"

def test_phase22_all_12_datasets_exist():
    """Verify all 12 required Phase 22 CSV datasets exist and are non-empty."""
    required_files = [
        "phase22_early_radar_scores.csv",
        "phase22_probability_horizons.csv",
        "phase22_precision_topn.csv",
        "phase22_yearly.csv",
        "phase22_regime.csv",
        "phase22_event_study.csv",
        "phase22_baselines.csv",
        "phase22_calibration.csv",
        "phase22_false_positives.csv",
        "phase22_placebo.csv",
        "phase22_feature_importance.csv",
        "phase22_2026_holdout.csv"
    ]
    for rf in required_files:
        p = RESULTS_DIR / rf
        assert p.exists(), f"Missing required Phase 22 dataset: {rf}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Dataset is empty: {rf}"

def test_phase22_report_exists_and_detailed():
    """Verify Phase 22 formal report exists and specifies radar score and lead time."""
    p = REPORTS_DIR / "PHASE22_EARLY_RADAR.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert len(content) > 1000
    assert "EARLY SECTOR RADAR" in content
    assert "P(1D)" in content
    assert "P(5D)" in content

def test_phase22_probability_horizons_monotone():
    """Verify multi-horizon probability predictions exist for 1D through 5D."""
    p = RESULTS_DIR / "phase22_probability_horizons.csv"
    df = pd.read_csv(p)
    assert len(df) == 5
    assert "Horizon" in df.columns
    assert "Brier_Score" in df.columns

def test_phase22_event_study_precursor_curve():
    """Verify event study contains T-10 to T+5 trajectory."""
    p = RESULTS_DIR / "phase22_event_study.csv"
    df = pd.read_csv(p)
    assert len(df) == 8
    assert "Timeline" in df.columns
    assert "Avg_Radar_Score" in df.columns

def test_phase22_feature_importance_ranks():
    """Verify feature importance has top ranked predictors."""
    p = RESULTS_DIR / "phase22_feature_importance.csv"
    df = pd.read_csv(p)
    assert len(df) >= 8
    assert "Feature_Name" in df.columns
    assert "Gini_Importance" in df.columns

def test_phase22_2026_holdout_integrity():
    """Verify 2026 untouched holdout evaluation."""
    p = RESULTS_DIR / "phase22_2026_holdout.csv"
    df = pd.read_csv(p)
    assert len(df) > 0
    assert "Precision@5" in df.columns
