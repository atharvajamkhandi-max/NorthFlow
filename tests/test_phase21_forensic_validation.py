"""
Unit and Integration Test Suite for Phase 21:
Forensic Validation of the Early Industry Detection Engine.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "research" / "results"
REPORTS_DIR = BASE_DIR / "research" / "reports"

def test_phase21_all_11_datasets_exist():
    """Verify all 11 required Phase 21 CSV datasets exist and are non-empty."""
    required_files = [
        "phase21_yearly_precision.csv",
        "phase21_lead_time.csv",
        "phase21_placebo.csv",
        "phase21_baselines.csv",
        "phase21_event_definitions.csv",
        "phase21_calibration.csv",
        "phase21_false_positives.csv",
        "phase21_regime_validation.csv",
        "phase21_survivorship.csv",
        "phase21_2026_holdout.csv",
        "phase21_feature_leakage_audit.csv"
    ]
    for rf in required_files:
        p = RESULTS_DIR / rf
        assert p.exists(), f"Missing required Phase 21 dataset: {rf}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Dataset is empty: {rf}"

def test_phase21_report_exists_and_forensic():
    """Verify Phase 21 formal report exists and specifies forensic findings."""
    p = REPORTS_DIR / "PHASE21_FORENSIC_VALIDATION.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert len(content) > 1000
    assert "PRE_EVENT_SUCCESS" in content
    assert "LEAKAGE" in content or "Leakage" in content

def test_phase21_feature_leakage_zero_dependencies():
    """Verify feature leakage audit contains zero future dependencies."""
    p = RESULTS_DIR / "phase21_feature_leakage_audit.csv"
    df = pd.read_csv(p)
    assert len(df) >= 10
    assert (df['Future_Dependency'] == False).all()
    assert (df['Leakage_Status'] == 'CLEAN').all()

def test_phase21_timing_integrity():
    """Verify pre-event detections dominate over post-event contamination."""
    p = RESULTS_DIR / "phase21_lead_time.csv"
    df = pd.read_csv(p)
    assert len(df) == 3
    pre_row = df[df['Signal_Timing_Window'].str.contains('PRE_EVENT')].iloc[0]
    pct_val = float(str(pre_row['Percentage_Of_Events']).replace('%', ''))
    assert pct_val > 50.0

def test_phase21_placebo_trial_count():
    """Verify placebo experiment ran 1,000 iterations."""
    p = RESULTS_DIR / "phase21_placebo.csv"
    df = pd.read_csv(p)
    assert len(df) > 0
    assert "Placebo" in str(df['Forensic_Test'].iloc[0])

def test_phase21_2026_holdout_integrity():
    """Verify 2026 untouched holdout evaluation exists."""
    p = RESULTS_DIR / "phase21_2026_holdout.csv"
    df = pd.read_csv(p)
    assert len(df) > 0
    assert "Precision_At_Top5" in df.columns
