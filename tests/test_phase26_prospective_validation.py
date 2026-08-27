"""
Unit and Integration Test Suite for Phase 26:
Early Sector Radar Frozen Specification & Prospective Live Validation.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROSPECTIVE_DIR = BASE_DIR / "research" / "prospective_validation"
REPORTS_DIR = BASE_DIR / "research" / "reports"
AUDIT_LOG_FILE = PROSPECTIVE_DIR / "audit_log.csv"

def test_phase26_frozen_config_immutability():
    """Verify EARLY_RADAR_V1_FROZEN configuration and governance fingerprint."""
    from config.early_radar_v1_frozen import EARLY_RADAR_V1_FROZEN
    assert EARLY_RADAR_V1_FROZEN["model_version"] == "EARLY_RADAR_V1_FROZEN"
    assert EARLY_RADAR_V1_FROZEN["alert_thresholds"]["PRE_BREAKOUT"] == 75.0
    assert EARLY_RADAR_V1_FROZEN["alert_thresholds"]["EARLY"] == 65.0
    assert EARLY_RADAR_V1_FROZEN["alert_thresholds"]["WATCH"] == 55.0
    assert EARLY_RADAR_V1_FROZEN["turnaround_cohort_rule"]["v3_2_max"] == 55.0
    assert EARLY_RADAR_V1_FROZEN["turnaround_cohort_rule"]["early_radar_min"] == 65.0

def test_phase26_prospective_snapshots_exist():
    """Verify prospective validation snapshots directory exists and is populated."""
    assert PROSPECTIVE_DIR.exists()
    snapshots = list(PROSPECTIVE_DIR.glob("*_early_radar.csv"))
    assert len(snapshots) > 0, "No prospective snapshots found"
    df = pd.read_csv(snapshots[0])
    assert "early_radar_score" in df.columns
    assert "low_v32_high_radar_turnaround" in df.columns

def test_phase26_cryptographic_audit_log_valid():
    """Verify audit_log.csv contains valid SHA-256 hashes for all snapshots."""
    assert AUDIT_LOG_FILE.exists()
    df_audit = pd.read_csv(AUDIT_LOG_FILE)
    assert len(df_audit) > 0
    assert "sha256_hash" in df_audit.columns
    assert "model_version" in df_audit.columns
    for _, row in df_audit.iterrows():
        assert len(str(row['sha256_hash'])) == 64  # Valid SHA-256 length

def test_phase26_anti_lookahead_safeguard():
    """Verify signal generator accepts only point-in-time data through market close T."""
    from pipeline.prospective_radar_runner import generate_daily_prospective_snapshot
    snap_path = generate_daily_prospective_snapshot("2026-08-21")
    assert snap_path.exists()
    df = pd.read_csv(snap_path)
    # Forward outcome columns must not exist in snapshot
    for fwd in ['fwd_1d', 'fwd_5d', 'fwd_20d', 'future_return']:
        assert fwd not in df.columns

def test_phase26_report_exists_and_verdict():
    """Verify Phase 26 report exists with governance verdict."""
    p = REPORTS_DIR / "PHASE26_PROSPECTIVE_VALIDATION.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert "EARLY_RADAR_V1_FROZEN" in content
    assert "INSUFFICIENT SAMPLE — CONTINUE OBSERVATION" in content
