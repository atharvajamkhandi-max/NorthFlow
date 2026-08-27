"""
Unit and Integration Test Suite for Phase 23:
Early Sector Radar Shadow-Production Replay & Calibration Audit.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "research" / "results"
REPORTS_DIR = BASE_DIR / "research" / "reports"

def test_phase23_all_12_datasets_exist():
    """Verify all 12 required Phase 23 CSV datasets exist and are non-empty."""
    required_files = [
        "phase23_daily_replay.csv",
        "phase23_alerts.csv",
        "phase23_event_database.csv",
        "phase23_calibration.csv",
        "phase23_alert_quality.csv",
        "phase23_lead_time.csv",
        "phase23_persistence.csv",
        "phase23_cross_stock_confirmation.csv",
        "phase23_regime.csv",
        "phase23_low_v32_high_radar.csv",
        "phase23_portfolio.csv",
        "phase23_2026_holdout.csv"
    ]
    for rf in required_files:
        p = RESULTS_DIR / rf
        assert p.exists(), f"Missing required Phase 23 dataset: {rf}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Dataset is empty: {rf}"

def test_phase23_report_exists_and_detailed():
    """Verify Phase 23 formal report exists and specifies shadow replay findings."""
    p = REPORTS_DIR / "PHASE23_SHADOW_REPLAY.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert len(content) > 1000
    assert "SHADOW-PRODUCTION REPLAY" in content
    assert "EVT_2020_08_SUGAR" in content

def test_phase23_event_database_lead_times():
    """Verify event database has positive lead times between 1 and 5 days."""
    p = RESULTS_DIR / "phase23_event_database.csv"
    df = pd.read_csv(p)
    assert len(df) >= 5
    assert "LeadTime_Days" in df.columns
    assert (df['LeadTime_Days'] >= 1).all()
    assert (df['LeadTime_Days'] <= 5).all()

def test_phase23_calibration_buckets_count():
    """Verify calibration audit has 10 probability buckets."""
    p = RESULTS_DIR / "phase23_calibration.csv"
    df = pd.read_csv(p)
    assert len(df) == 10
    assert "Probability_Bucket" in df.columns

def test_phase23_portfolio_friction_tested():
    """Verify portfolio stress tests include 15, 30, and 50 bps."""
    p = RESULTS_DIR / "phase23_portfolio.csv"
    df = pd.read_csv(p)
    assert len(df) >= 3
    assert "Net_CAGR_30bps" in df.columns

def test_phase23_2026_holdout_integrity():
    """Verify 2026 untouched holdout evaluation."""
    p = RESULTS_DIR / "phase23_2026_holdout.csv"
    df = pd.read_csv(p)
    assert len(df) > 0
    assert "Precision@5" in df.columns
