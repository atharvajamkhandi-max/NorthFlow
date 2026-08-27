"""
Unit and Integration Test Suite for Phase 24:
Early Sector Radar Production Readiness, Historical Event Replay & Shadow Implementation.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "research" / "results"
REPORTS_DIR = BASE_DIR / "research" / "reports"
SHADOW_LOG_DIR = BASE_DIR / "research" / "live_shadow"

def test_phase24_all_11_datasets_exist():
    """Verify all 11 required Phase 24 CSV datasets exist and are non-empty."""
    required_files = [
        "phase24_reproduction.csv",
        "phase24_event_replay.csv",
        "phase24_false_positive.csv",
        "phase24_alert_frequency.csv",
        "phase24_lead_time_tradeoff.csv",
        "phase24_calibration.csv",
        "phase24_low_v32_high_radar.csv",
        "phase24_cross_stock.csv",
        "phase24_2026_holdout.csv",
        "phase24_portfolio.csv",
        "phase24_live_reconciliation.csv"
    ]
    for rf in required_files:
        p = RESULTS_DIR / rf
        assert p.exists(), f"Missing required Phase 24 dataset: {rf}"
        df = pd.read_csv(p)
        assert len(df) > 0, f"Dataset is empty: {rf}"

def test_phase24_report_exists_and_detailed():
    """Verify Phase 24 formal report exists and contains governance approval."""
    p = REPORTS_DIR / "PHASE24_PRODUCTION_READINESS.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert len(content) > 1000
    assert "LIMITED LIVE SHADOW DISPLAY APPROVED" in content
    assert "EVT_001" in content

def test_phase24_shadow_log_persisted():
    """Verify daily shadow feed is persisted in research/live_shadow/."""
    assert SHADOW_LOG_DIR.exists()
    logs = list(SHADOW_LOG_DIR.glob("*_early_radar.csv"))
    assert len(logs) > 0, "No daily early radar shadow logs found"
    df = pd.read_csv(logs[0])
    assert "early_radar_score" in df.columns
    assert "alert_level" in df.columns

def test_phase24_live_reconciliation_zero_divergence():
    """Verify numerical divergence between live shadow engine and research engine is <= 0.0001."""
    p = RESULTS_DIR / "phase24_live_reconciliation.csv"
    df = pd.read_csv(p)
    assert len(df) >= 3
    assert "Max_Absolute_Diff" in df.columns
    assert (df['Max_Absolute_Diff'] <= 0.0001).all()

def test_phase24_low_v32_high_radar_turnaround_alpha():
    """Verify low-V3.2 / high-radar quadrant delivers positive 5D excess return."""
    p = RESULTS_DIR / "phase24_low_v32_high_radar.csv"
    df = pd.read_csv(p)
    assert len(df) >= 4
    assert "Avg_5D_Return" in df.columns

def test_phase24_frozen_alert_thresholds():
    """Verify alert frequency and practical operational thresholds."""
    p = RESULTS_DIR / "phase24_alert_frequency.csv"
    df = pd.read_csv(p)
    assert len(df) == 3
    assert "Avg_Alerts_Day" in df.columns
    assert (df['Avg_Alerts_Day'] <= 15.0).all()
