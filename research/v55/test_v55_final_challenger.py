"""
research/v55/test_v55_final_challenger.py
Isolated unit tests for Phase 55 Final Challenger Audit.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE55_DIR = Path(__file__).resolve().parent

def test_1_scorecard_and_holdout_files_exist():
    s_file = PHASE55_DIR / "challenger_audit" / "primary_decision_criteria_scorecard.csv"
    h_file = PHASE55_DIR / "locked_holdout" / "tier_c_holdout_scorecard.csv"
    assert s_file.exists()
    assert h_file.exists()
    df_s = pd.read_csv(s_file)
    df_h = pd.read_csv(h_file)
    assert len(df_s) == 5
    assert len(df_h) == 5

def test_2_anti_leakage_16_vectors_caught():
    l_file = PHASE55_DIR / "anti_leakage" / "anti_leakage_attack_results.json"
    assert l_file.exists()
    with open(l_file, "r") as f:
        data = json.load(f)
    assert len(data) == 17
    for k, v in data.items():
        if k != "clean_baseline_check":
            assert v["status"] == "CAUGHT_AND_BLOCKED"
    assert data["clean_baseline_check"]["status"] == "CLEAN_0_LEAKAGE"

def test_3_v34_ta_veto_achieves_highest_net_spread():
    s_file = PHASE55_DIR / "challenger_audit" / "primary_decision_criteria_scorecard.csv"
    df = pd.read_csv(s_file)
    b_row = df[df["architecture"] == "Arch_B_V34_TA_Veto"].iloc[0]
    e_row = df[df["architecture"] == "Arch_E_Dynamic_Router"].iloc[0]
    assert b_row["net_spread_bps"] > e_row["net_spread_bps"]
    assert b_row["net_spread_bps"] >= 290.0

def test_4_dynamic_router_dilution_forensic_identified():
    d_file = PHASE55_DIR / "router_forensics" / "dynamic_router_dilution_forensic.json"
    assert d_file.exists()
    with open(d_file, "r") as f:
        data = json.load(f)
    assert data["dilution_cost_bps"] < 0.0
    assert "Inversion" in data["finding"]

def test_5_final_decision_is_arch_b_v34_ta_veto():
    f_file = PHASE55_DIR / "challenger_audit" / "final_decision.json"
    assert f_file.exists()
    with open(f_file, "r") as f:
        data = json.load(f)
    assert data["selected_architecture"].startswith("B. V3.4 + TA VETO")
