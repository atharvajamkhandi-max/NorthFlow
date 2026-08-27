"""
research/v49/test_v49_historical_replay.py
Isolated unit tests for Phase 49 Day-by-Day Historical Market Replay Engine.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE49_DIR = Path(__file__).resolve().parent

def test_1_day_by_day_predictions_and_outcomes_exist():
    p_file = PHASE49_DIR / "day_by_day_predictions.csv"
    o_file = PHASE49_DIR / "day_by_day_outcomes.csv"
    assert p_file.exists()
    assert o_file.exists()
    df_p = pd.read_csv(p_file)
    df_o = pd.read_csv(o_file)
    assert len(df_p) > 20000
    assert len(df_o) > 20000
    assert len(df_p) == len(df_o)

def test_2_leakage_detector_passed():
    l_file = PHASE49_DIR / "leakage_test_results.json"
    assert l_file.exists()
    with open(l_file, "r") as f:
        data = json.load(f)
    assert data["detector_status"] == "PASSED"
    assert data["clean_dataset_leakage_detected"] is False
    assert data["corrupted_dataset_leakage_detected"] is True

def test_3_v34_superiority_in_replay():
    c_file = PHASE49_DIR / "v32_vs_v34_comparison.csv"
    assert c_file.exists()
    df_c = pd.read_csv(c_file)
    acc_row = df_c[df_c["metric"].str.contains("Accuracy")].iloc[0]
    mae_row = df_c[df_c["metric"].str.contains("MAE")].iloc[0]
    assert acc_row["v34_candidate"] > acc_row["v32_baseline"]
    assert mae_row["v34_candidate"] < mae_row["v32_baseline"]

def test_4_portfolio_net_spread_positive():
    p_file = PHASE49_DIR / "portfolio_results.csv"
    assert p_file.exists()
    df_p = pd.read_csv(p_file)
    net_row = df_p[df_p["strategy"].str.contains("Net")].iloc[0]
    assert net_row["mean_return_bps"] > 200.0

def test_5_reproducibility_100_percent():
    r_file = PHASE49_DIR / "reproducibility_results.json"
    assert r_file.exists()
    with open(r_file, "r") as f:
        data = json.load(f)
    assert data["bit_exact_match"] is True
