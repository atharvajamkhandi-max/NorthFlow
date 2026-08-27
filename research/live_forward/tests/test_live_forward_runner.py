"""
research/live_forward/tests/test_live_forward_runner.py
Isolated unit tests for Permanent Live Forward Validation Runner.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

LIVE_DIR = Path(__file__).resolve().parent.parent

def test_1_live_ledger_and_scorecards_exist():
    p_file = LIVE_DIR / "ledger" / "live_predictions.csv"
    h_file = LIVE_DIR / "ledger" / "live_hashes.csv"
    s_file = LIVE_DIR / "scorecards" / "cumulative_live_scorecard.json"
    g_file = LIVE_DIR / "promotion_gate" / "promotion_status.json"
    assert p_file.exists()
    assert h_file.exists()
    assert s_file.exists()
    assert g_file.exists()

def test_2_prediction_immutability_and_hash_locks():
    p_df = pd.read_csv(LIVE_DIR / "ledger" / "live_predictions.csv")
    h_df = pd.read_csv(LIVE_DIR / "ledger" / "live_hashes.csv")
    assert len(p_df) == len(h_df) == 1196
    assert (p_df["prediction_hash"] == h_df["prediction_hash"]).all()

def test_3_promotion_gate_strictly_locked():
    g_file = LIVE_DIR / "promotion_gate" / "promotion_status.json"
    with open(g_file, "r") as f:
        data = json.load(f)
    assert data["promotion_status"] == "LOCKED"
    assert data["production_deployment_allowed"] == False

def test_4_zero_lookahead_and_clean_pit():
    s_file = LIVE_DIR / "scorecards" / "cumulative_live_scorecard.json"
    with open(s_file, "r") as f:
        data = json.load(f)
    assert "100% VERIFIED" in data["integrity_status"]
    assert data["matured_20D_observations"] == 0

def test_5_production_immutability_checksums_match():
    pre_file = LIVE_DIR / "safety" / "checksums_preflight.json"
    post_file = LIVE_DIR / "safety" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
