"""
research/v54/test_v54_evidence_router.py
Isolated unit tests for Phase 54 NorthFlow Evidence Router Tournament.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE54_DIR = Path(__file__).resolve().parent

def test_1_candidate_scorecard_and_specialization_table_exist():
    c_file = PHASE54_DIR / "historical_replay" / "candidate_configurations_scorecard.csv"
    s_file = PHASE54_DIR / "router_engine" / "final_model_specialization_table.csv"
    assert c_file.exists()
    assert s_file.exists()
    df_c = pd.read_csv(c_file)
    df_s = pd.read_csv(s_file)
    assert len(df_c) == 7
    assert len(df_s) == 3

def test_2_anti_leakage_10_vectors_caught():
    l_file = PHASE54_DIR / "anti_leakage" / "anti_leakage_attack_results.json"
    assert l_file.exists()
    with open(l_file, "r") as f:
        data = json.load(f)
    assert len(data) == 11
    for k, v in data.items():
        if k != "clean_baseline_check":
            assert v["status"] == "CAUGHT_AND_BLOCKED"
    assert data["clean_baseline_check"]["status"] == "CLEAN_0_LEAKAGE"

def test_3_dynamic_router_outperforms_v32_baseline():
    c_file = PHASE54_DIR / "historical_replay" / "candidate_configurations_scorecard.csv"
    df = pd.read_csv(c_file)
    v32_acc = df[df["configuration"] == "Config_A_V32_Only"]["directional_accuracy_pct"].iloc[0]
    dyn_acc = df[df["configuration"] == "Config_G_Dynamic_Router"]["directional_accuracy_pct"].iloc[0]
    assert dyn_acc > v32_acc
    assert dyn_acc >= 58.0

def test_4_model_specialization_roles_integrity():
    s_file = PHASE54_DIR / "router_engine" / "final_model_specialization_table.csv"
    df = pd.read_csv(s_file)
    ta_row = df[df["model"].str.contains("TradingAgents")].iloc[0]
    assert "Risk" in ta_row["primary_job"]
    assert "Numerical" in ta_row["forbidden_job"]

def test_5_tournament_verdict_is_dynamic_evidence_router():
    v_file = PHASE54_DIR / "router_engine" / "final_verdict.json"
    assert v_file.exists()
    with open(v_file, "r") as f:
        data = json.load(f)
    assert data["tournament_winner"].startswith("E. Dynamic Evidence Router")
