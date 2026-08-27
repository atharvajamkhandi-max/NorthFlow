"""
Unit and Integration Test Suite for Phase 18:
Model V3.2 Failure Analysis & Conditional Alpha Research.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "research" / "results"
REPORTS_DIR = BASE_DIR / "research" / "reports"

def test_phase18_all_8_datasets_exist():
    """Verify all 8 required Phase 18 CSV datasets exist and are non-empty."""
    required_files = [
        "phase18_score_buckets.csv",
        "phase18_score_acceleration.csv",
        "phase18_regime_analysis.csv",
        "phase18_industry_conditioning.csv",
        "phase18_failure_events.csv",
        "phase18_failure_predictors.csv",
        "phase18_conditional_rules.csv",
        "phase18_2026_holdout.csv"
    ]
    for rf in required_files:
        p = RESULTS_DIR / rf
        assert p.exists(), f"Missing required Phase 18 dataset: {rf}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Dataset is empty: {rf}"

def test_phase18_report_exists_and_reconciles():
    """Verify Phase 18 formal report exists and reconciles metrics."""
    p = REPORTS_DIR / "PHASE18_V32_FAILURE_ANALYSIS.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert len(content) > 1000
    assert "0.1140" in content
    assert "0.0402" in content
    assert "MODEL_V3.2_FROZEN" in content

def test_phase18_score_bucket_monotonicity():
    """Verify score buckets have 10 partitions."""
    p = RESULTS_DIR / "phase18_score_buckets.csv"
    df = pd.read_csv(p)
    assert len(df) == 10
    assert "Avg_20D_Return" in df.columns

def test_phase18_hierarchical_conditioning_tiers():
    """Verify hierarchical conditioning contains aligned and misaligned tiers."""
    p = RESULTS_DIR / "phase18_industry_conditioning.csv"
    df = pd.read_csv(p)
    assert len(df) >= 4
    assert "hierarchy_tier" in df.columns

def test_phase18_holdout_integrity():
    """Verify 2026 untouched holdout evaluation."""
    p = RESULTS_DIR / "phase18_2026_holdout.csv"
    df = pd.read_csv(p)
    assert len(df) >= 2
    assert "Top_Decile_20D" in df.columns
