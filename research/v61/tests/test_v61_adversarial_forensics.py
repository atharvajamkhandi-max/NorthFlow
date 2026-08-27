"""
research/v61/tests/test_v61_adversarial_forensics.py
Isolated unit tests for Phase 61 Adversarial Forecast Forensics & Reality Audit.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE61_DIR = Path(__file__).resolve().parent.parent

def test_1_all_15_required_audit_csv_artifacts_exist():
    files = [
        "walk_forward_integrity_audit.csv", "survivorship_bias_audit.csv", "corporate_action_audit.csv",
        "data_quality_audit.csv", "benchmark_reconciliation.csv", "strength_calibration_audit.csv",
        "recommendation_audit.csv", "sector_rank_audit.csv", "model_comparison_audit.csv",
        "tradingagents_veto_audit.csv", "worst_predictions.csv", "best_predictions.csv",
        "software_stress_audit.csv", "data_fetch_audit.csv", "phase60_claim_verification.csv"
    ]
    for f_name in files:
        f_path = PHASE61_DIR / f_name
        assert f_path.exists(), f"Missing required audit artifact: {f_name}"
        df = pd.read_csv(f_path)
        assert len(df) > 0, f"Audit artifact is empty: {f_name}"

def test_2_walk_forward_integrity_zero_lookahead():
    w_df = pd.read_csv(PHASE61_DIR / "walk_forward_integrity_audit.csv")
    assert len(w_df) == 500
    assert (w_df["lookahead_detected"] == False).all()
    assert (w_df["pit_compliance"] == "VERIFIED_CLEAN").all()

def test_3_benchmark_reconciliation_exact_match():
    b_df = pd.read_csv(PHASE61_DIR / "benchmark_reconciliation.csv")
    for idx, row in b_df.iterrows():
        assert row["status"] == "VERIFIED_EXACT"

def test_4_worst_and_best_100_predictions_populated():
    w_df = pd.read_csv(PHASE61_DIR / "worst_predictions.csv")
    b_df = pd.read_csv(PHASE61_DIR / "best_predictions.csv")
    assert len(w_df) == 100
    assert len(b_df) == 100
    assert "failure_reason" in w_df.columns
    assert "success_driver" in b_df.columns

def test_5_production_immutability_checksums_match():
    pre_file = PHASE61_DIR / "checksums_preflight.json"
    post_file = PHASE61_DIR / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
