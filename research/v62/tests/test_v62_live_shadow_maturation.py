"""
research/v62/tests/test_v62_live_shadow_maturation.py
Isolated unit tests for Phase 62 Prospective Live Shadow Maturation Engine.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE62_DIR = Path(__file__).resolve().parent.parent

def test_1_all_required_live_artifacts_exist():
    files = [
        "live_ledger/predictions.csv", "live_ledger/prediction_hashes.csv",
        "live_ledger/source_snapshot.csv", "live_ledger/daily_run_log.csv",
        "maturation/maturation_ledger.csv", "forensics/best_predictions.csv",
        "forensics/worst_predictions.csv", "scorecards/daily_model_scorecard.csv",
        "scorecards/regime_scorecard.csv", "system_health/daily_system_health.csv",
        "promotion_gate/live_maturity_progress.csv", "promotion_gate/promotion_status.json",
        "safety/production_immutability_audit.json"
    ]
    for f_name in files:
        f_path = PHASE62_DIR / f_name
        assert f_path.exists(), f"Missing required live shadow artifact: {f_name}"

def test_2_prediction_immutability_and_hash_locks():
    p_df = pd.read_csv(PHASE62_DIR / "live_ledger" / "predictions.csv")
    h_df = pd.read_csv(PHASE62_DIR / "live_ledger" / "prediction_hashes.csv")
    assert len(p_df) == len(h_df)
    assert (p_df["prediction_hash"] == h_df["prediction_hash"]).all()
    assert (h_df["immutable_lock"] == True).all()

def test_3_promotion_gate_status_is_not_ready():
    p_file = PHASE62_DIR / "promotion_gate" / "promotion_status.json"
    with open(p_file, "r") as f:
        data = json.load(f)
    assert data["promotion_gate_decision"] == "NOT_READY"
    assert "INSUFFICIENT_SAMPLE" in data["live_evidence_classification"]
    assert data["active_production_model"] == "MODEL_V3.2_FROZEN (100% UNCHANGED)"

def test_4_daily_system_health_clean():
    h_df = pd.read_csv(PHASE62_DIR / "system_health" / "daily_system_health.csv")
    assert len(h_df) == 4
    assert (h_df["pit_violations"] == 0).all()
    assert (h_df["duplicate_predictions_rejected"] == 0).all()
    assert (h_df["system_health_status"] == "OPTIMAL_HEALTHY").all()

def test_5_production_immutability_checksums_match():
    a_file = PHASE62_DIR / "safety" / "production_immutability_audit.json"
    with open(a_file, "r") as f:
        audit = json.load(f)
    assert audit["production_models_modified"] == 0
    assert audit["checksums_identical"] == True
