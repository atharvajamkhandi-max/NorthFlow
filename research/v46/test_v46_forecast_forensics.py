"""
research/v46/test_v46_forecast_forensics.py
Isolated research unit tests for Phase 46 Forecast-Math Forensics and Economic Backtest Audit.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE46_DIR = Path(__file__).resolve().parent

def test_1_price_target_arithmetic_forensics():
    s_file = PHASE46_DIR / "forensic_results" / "price_target_forensic_cases_sample.json"
    assert s_file.exists()
    with open(s_file, "r") as f:
        cases = json.load(f)
    assert len(cases) >= 10
    for c in cases:
        base = c["base_price"]
        pred_ret = c["pred_return_pct"]
        target = c["target_price"]
        expected_target = base * (1.0 + pred_ret / 100.0)
        assert abs(target - expected_target) < 0.05

def test_2_economic_anomaly_reconciliation():
    a_file = PHASE46_DIR / "forensic_results" / "economic_anomaly_reconciliation.json"
    assert a_file.exists()
    with open(a_file, "r") as f:
        data = json.load(f)
    assert data["true_spread_bps"] > 300.0
    assert "Double multiplication" in data["root_cause"]

def test_3_conformal_scaling_multiplier_integrity():
    c_file = PHASE46_DIR / "forensic_results" / "conformal_scaling_audit.json"
    assert c_file.exists()
    with open(c_file, "r") as f:
        data = json.load(f)
    assert data["conformal_multiplier"] == 1.30
    assert data["calibrated_coverage_pct"] >= 75.0
    assert data["interval_monotonicity"] is True

def test_4_20d_metrics_magnitude_and_ranking():
    m_file = PHASE46_DIR / "forensic_results" / "metrics_20d_validation.json"
    assert m_file.exists()
    with open(m_file, "r") as f:
        data = json.load(f)
    assert data["spearman_rank_ic"] > 0.10
    assert data["directional_accuracy_pct"] > 60.0
    assert data["mae_pct"] < 9.0

def test_5_phase46_isolation():
    assert (PHASE46_DIR / "sandbox").exists()
    assert (PHASE46_DIR / "forensic_results").exists()
