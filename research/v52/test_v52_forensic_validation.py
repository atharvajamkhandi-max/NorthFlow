"""
research/v52/test_v52_forensic_validation.py
Isolated unit tests for Phase 52 Final Independent Forensic Time-Machine Validation.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE52_DIR = Path(__file__).resolve().parent

def test_1_exact_prediction_and_outcome_ledgers_exist():
    p_file = PHASE52_DIR / "exact_prediction_ledger.csv"
    o_file = PHASE52_DIR / "actual_outcome_ledger.csv"
    assert p_file.exists()
    assert o_file.exists()
    df_p = pd.read_csv(p_file)
    df_o = pd.read_csv(o_file)
    assert len(df_p) > 25000
    assert len(df_o) == len(df_p)

def test_2_anti_leakage_attack_caught_all_8_vectors():
    l_file = PHASE52_DIR / "audit_results" / "anti_leakage_attack_results.json"
    assert l_file.exists()
    with open(l_file, "r") as f:
        data = json.load(f)
    for k, v in data.items():
        if k != "clean_baseline_check":
            assert v["status"] == "CAUGHT_AND_BLOCKED"
    assert data["clean_baseline_check"]["status"] == "CLEAN_0_LEAKAGE"

def test_3_decision_matrix_v34_wins_majority_disagreements():
    p_file = PHASE52_DIR / "exact_prediction_ledger.csv"
    df = pd.read_csv(p_file)
    v34_wins = (df["decision_state"] == "V34_WIN").sum()
    v32_wins = (df["decision_state"] == "V32_WIN").sum()
    assert v34_wins > v32_wins
    assert (v34_wins / (v34_wins + v32_wins)) > 0.55

def test_4_statistical_significance_mae_reduction():
    s_file = PHASE52_DIR / "audit_results" / "statistical_inference.json"
    assert s_file.exists()
    with open(s_file, "r") as f:
        data = json.load(f)
    assert data["mae_reduction_95_ci_pp"][0] > 0.0
    assert data["directional_acc_gain_mean_pp"] > 0.0

def test_5_reproducibility_bit_exact():
    r_file = PHASE52_DIR / "audit_results" / "reproducibility_hashes.json"
    assert r_file.exists()
    with open(r_file, "r") as f:
        data = json.load(f)
    assert data["bit_exact_match"] is True
