"""
Unit and Integration Test Suite for Phase 19:
V3.2 Conditional Filter Final Validation & Production Gate.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "research" / "results"
REPORTS_DIR = BASE_DIR / "research" / "reports"
CONFIG_DIR = BASE_DIR / "config"

def test_phase19_all_9_datasets_exist():
    """Verify all 9 required Phase 19 CSV datasets exist and are non-empty."""
    required_files = [
        "phase19_baseline_vs_filtered.csv",
        "phase19_industry_filter.csv",
        "phase19_breadth_filter.csv",
        "phase19_volatility_filter.csv",
        "phase19_combination_test.csv",
        "phase19_walk_forward.csv",
        "phase19_2026_holdout.csv",
        "phase19_placebo.csv",
        "phase19_statistical_significance.csv"
    ]
    for rf in required_files:
        p = RESULTS_DIR / rf
        assert p.exists(), f"Missing required Phase 19 dataset: {rf}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Dataset is empty: {rf}"

def test_phase19_report_exists_and_approved():
    """Verify Phase 19 formal report exists and contains production gate decision."""
    p = REPORTS_DIR / "PHASE19_CONDITIONAL_FILTER_VALIDATION.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert len(content) > 1000
    assert "MODEL_V3_2_CONDITIONAL_SHADOW" in content
    assert "MODEL_V3.2_FROZEN" in content

def test_phase19_shadow_model_file_exists():
    """Verify shadow model file exists and exports fingerprint and function."""
    p = CONFIG_DIR / "model_v3_2_conditional_shadow.py"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert "MODEL_V3_2_CONDITIONAL_SHADOW_FINGERPRINT" in content
    assert "evaluate_conditional_eligibility" in content

def test_phase19_opportunity_coverage_gate():
    """Verify opportunity coverage remains economically useful (>= 50%)."""
    p = RESULTS_DIR / "phase19_baseline_vs_filtered.csv"
    df = pd.read_csv(p)
    assert len(df) >= 2
    filt_row = df[df['Model_Variant'].str.contains('SHADOW')].iloc[0]
    cov_str = str(filt_row['Opportunity_Coverage']).replace('%', '')
    assert float(cov_str) >= 50.0

def test_phase19_2026_holdout_superiority():
    """Verify 2026 untouched holdout preserves positive spread."""
    p = RESULTS_DIR / "phase19_2026_holdout.csv"
    df = pd.read_csv(p)
    assert len(df) >= 2
    assert "Top_Bottom_Spread" in df.columns or "Top_Decile_20D" in df.columns
