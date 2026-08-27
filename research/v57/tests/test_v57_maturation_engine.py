"""
research/v57/tests/test_v57_maturation_engine.py
Isolated unit tests for Phase 57 Immutable Live-Shadow Maturation & Model Scorecard Engine.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE57_DIR = Path(__file__).resolve().parent.parent

def test_1_scorecards_and_regime_analysis_exist():
    s_file = PHASE57_DIR / "scorecards" / "three_way_side_by_side_scorecard.csv"
    r_file = PHASE57_DIR / "regime_analysis" / "regime_conditional_scorecard.csv"
    assert s_file.exists()
    assert r_file.exists()
    df_s = pd.read_csv(s_file)
    assert len(df_s) == 3

def test_2_anti_leakage_16_vectors_caught():
    l_file = PHASE57_DIR / "audit" / "anti_leakage_attack_results.json"
    assert l_file.exists()
    with open(l_file, "r") as f:
        data = json.load(f)
    assert len(data) == 17
    for k, v in data.items():
        if k != "clean_baseline_check":
            assert v["status"] == "CAUGHT_AND_BLOCKED"
    assert data["clean_baseline_check"]["status"] == "CLEAN_0_LEAKAGE"

def test_3_three_way_scorecard_v34_ta_leads():
    s_file = PHASE57_DIR / "scorecards" / "three_way_side_by_side_scorecard.csv"
    df = pd.read_csv(s_file)
    ta_row = df[df["model_architecture"] == "C_MODEL_V34_TA_VETO_SHADOW"].iloc[0]
    v32_row = df[df["model_architecture"] == "A_MODEL_V32_FROZEN"].iloc[0]
    assert ta_row["net_spread_bps"] > v32_row["net_spread_bps"]
    assert ta_row["spearman_rank_ic"] > v32_row["spearman_rank_ic"]

def test_4_promotion_gate_status_not_enough_live_evidence():
    p_file = PHASE57_DIR / "promotion_gate" / "promotion_gate_decision.json"
    assert p_file.exists()
    with open(p_file, "r") as f:
        data = json.load(f)
    assert data["gate_status"] == "NOT_ENOUGH_LIVE_EVIDENCE"
    assert data["gate_criteria"]["A_minimum_live_sessions"]["passed"] is False

def test_5_production_immutability_checksums_match():
    pre_file = PHASE57_DIR / "audit" / "checksums_preflight.json"
    post_file = PHASE57_DIR / "audit" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
