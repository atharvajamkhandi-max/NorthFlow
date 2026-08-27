"""
Unit and Integration Test Suite for Phase 20:
Early Sector/Industry Lead-Time Detection Engine.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "research" / "results"
REPORTS_DIR = BASE_DIR / "research" / "reports"

def test_phase20_all_11_datasets_exist():
    """Verify all 11 required Phase 20 CSV datasets exist and are non-empty."""
    required_files = [
        "phase20_event_definition.csv",
        "phase20_lead_lag.csv",
        "phase20_event_study.csv",
        "phase20_industry_signals.csv",
        "phase20_accumulation_pressure.csv",
        "phase20_pre_breakout.csv",
        "phase20_ml_tournament.csv",
        "phase20_precision_recall.csv",
        "phase20_false_positives.csv",
        "phase20_regime_results.csv",
        "phase20_2026_holdout.csv"
    ]
    for rf in required_files:
        p = RESULTS_DIR / rf
        assert p.exists(), f"Missing required Phase 20 dataset: {rf}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Dataset is empty: {rf}"

def test_phase20_report_exists():
    """Verify Phase 20 formal report exists and specifies lead time metrics."""
    p = REPORTS_DIR / "PHASE20_EARLY_INDUSTRY_DETECTION.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert len(content) > 1000
    assert "Accumulation Pressure" in content or "ACCUMULATION_PRESSURE" in content
    assert "PRE_BREAKOUT" in content

def test_phase20_event_definitions():
    """Verify 5 objective expansion events are defined."""
    p = RESULTS_DIR / "phase20_event_definition.csv"
    df = pd.read_csv(p)
    assert len(df) == 5
    assert "Event_Code" in df.columns

def test_phase20_lead_time_distribution():
    """Verify lead time distribution contains metrics."""
    p = RESULTS_DIR / "phase20_lead_lag.csv"
    df = pd.read_csv(p)
    assert len(df) > 0
    assert "Average_Lead_Time_Days" in df.columns

def test_phase20_lifecycle_states():
    """Verify 9 lifecycle states exist."""
    p = RESULTS_DIR / "phase20_industry_signals.csv"
    df = pd.read_csv(p)
    assert len(df) == 9
    assert "lifecycle_state" in df.columns

def test_phase20_2026_holdout_integrity():
    """Verify 2026 untouched holdout evaluation."""
    p = RESULTS_DIR / "phase20_2026_holdout.csv"
    df = pd.read_csv(p)
    assert len(df) > 0
    assert "Precision_At_Top5" in df.columns
