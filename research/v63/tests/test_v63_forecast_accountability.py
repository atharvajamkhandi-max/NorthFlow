"""
research/v63/tests/test_v63_forecast_accountability.py
Isolated unit tests for Phase 63 Daily Prospective Forecast Accountability Engine.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE63_DIR = Path(__file__).resolve().parent.parent

def test_1_all_required_accountability_artifacts_exist():
    files = [
        "live_ledger/predictions.csv", "live_ledger/prediction_hashes.csv",
        "matching/matched_outcomes.csv", "accountability/daily_forecast_accountability.csv",
        "calibration/forecast_strength_calibration.csv", "forensics/worst_100_predictions.csv",
        "forensics/best_100_predictions.csv", "scorecards/cumulative_live_scorecard.json",
        "system_health/daily_system_health.csv", "promotion_gate/promotion_status.json",
        "safety/production_immutability_audit.json"
    ]
    for f_name in files:
        f_path = PHASE63_DIR / f_name
        assert f_path.exists(), f"Missing required Phase 63 artifact: {f_name}"

def test_2_prediction_immutability_and_hash_consistency():
    p_df = pd.read_csv(PHASE63_DIR / "live_ledger" / "predictions.csv")
    h_df = pd.read_csv(PHASE63_DIR / "live_ledger" / "prediction_hashes.csv")
    assert len(p_df) == len(h_df) == 1196
    assert (p_df["prediction_hash"] == h_df["prediction_hash"]).all()

def test_3_matched_outcomes_reconcile():
    m_df = pd.read_csv(PHASE63_DIR / "matching" / "matched_outcomes.csv")
    assert len(m_df) == 1196
    matured_1d = m_df[m_df["maturation_horizon"] == "1D_MATURED"]
    assert len(matured_1d) == 299
    assert (matured_1d["actual_return_1D"].notna()).all()

def test_4_promotion_gate_locked():
    p_file = PHASE63_DIR / "promotion_gate" / "promotion_status.json"
    with open(p_file, "r") as f:
        data = json.load(f)
    assert "LOCKED" in data["promotion_gate_status"]
    assert data["promotion_recommendation"] == "DO_NOT_PROMOTE"

def test_5_production_immutability_checksums_match():
    a_file = PHASE63_DIR / "safety" / "production_immutability_audit.json"
    with open(a_file, "r") as f:
        audit = json.load(f)
    assert audit["production_models_modified"] == 0
    assert audit["checksums_identical"] == True
