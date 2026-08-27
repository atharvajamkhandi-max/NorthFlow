"""
research/v51/test_v51_time_machine.py
Isolated unit tests for Phase 51 One-Year Historical Time-Machine Simulation & Model Tournament.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE51_DIR = Path(__file__).resolve().parent

def test_1_exact_prediction_ledger_exists_and_complete():
    p_file = PHASE51_DIR / "exact_prediction_ledger.csv"
    assert p_file.exists()
    df = pd.read_csv(p_file)
    assert len(df) > 25000
    assert "v32_expected_return" in df.columns
    assert "v33_expected_return" in df.columns
    assert "v34_expected_return" in df.columns
    assert "actual_20D_return" in df.columns

def test_2_anti_leakage_attack_caught_all_vectors():
    l_file = PHASE51_DIR / "time_machine_results" / "anti_leakage_attack_results.json"
    assert l_file.exists()
    with open(l_file, "r") as f:
        data = json.load(f)
    for k, v in data.items():
        if k != "clean_dataset_check":
            assert v["status"] == "CAUGHT_AND_BLOCKED"
    assert data["clean_dataset_check"]["status"] == "CLEAN_0_LEAKAGE"

def test_3_v34_superiority_in_tournament_scorecard():
    s_file = PHASE51_DIR / "time_machine_results" / "final_head_to_head_scorecard.csv"
    assert s_file.exists()
    df = pd.read_csv(s_file)
    acc_row = df[df["metric"].str.contains("Accuracy")].iloc[0]
    mae_row = df[df["metric"].str.contains("MAE")].iloc[0]
    assert acc_row["v34_hybrid"] > acc_row["v32_baseline"]
    assert mae_row["v34_hybrid"] < mae_row["v32_baseline"]

def test_4_bootstrap_statistical_significance():
    b_file = PHASE51_DIR / "time_machine_results" / "bootstrap_statistical_testing.json"
    assert b_file.exists()
    with open(b_file, "r") as f:
        data = json.load(f)
    assert data["n_bootstrap_iterations"] == 1000
    assert data["directional_acc_gain_mean_pp"] > 0.0
    assert data["mae_reduction_95_ci_pp"][0] > 0.0
