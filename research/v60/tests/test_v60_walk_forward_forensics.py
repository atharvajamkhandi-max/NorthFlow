"""
research/v60/tests/test_v60_walk_forward_forensics.py
Isolated unit tests for Phase 60 True Daily Walk-Forward Performance & Forecast Forensics.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE60_DIR = Path(__file__).resolve().parent.parent

def test_1_all_12_required_csv_artifacts_exist():
    files = [
        "daily_prediction_ledger.csv", "daily_actual_results.csv", "daily_deviation_ledger.csv",
        "stock_forecast_forensics.csv", "sector_forecast_forensics.csv", "strength_calibration.csv",
        "recommendation_results.csv", "model_comparison.csv", "failure_analysis.csv",
        "software_stress_results.csv", "data_fetch_stress_results.csv", "daily_system_health.csv"
    ]
    for f_name in files:
        f_path = PHASE60_DIR / f_name
        assert f_path.exists(), f"Missing required artifact: {f_name}"
        df = pd.read_csv(f_path)
        assert len(df) > 0, f"Artifact is empty: {f_name}"

def test_2_daily_prediction_and_actuals_reconcile():
    p_df = pd.read_csv(PHASE60_DIR / "daily_prediction_ledger.csv")
    a_df = pd.read_csv(PHASE60_DIR / "daily_actual_results.csv")
    d_df = pd.read_csv(PHASE60_DIR / "daily_deviation_ledger.csv")
    assert len(p_df) == len(a_df) == len(d_df)
    assert (p_df["prediction_id"] == a_df["prediction_id"]).all()
    assert (p_df["prediction_id"] == d_df["prediction_id"]).all()

def test_3_strength_calibration_monotonicity():
    c_df = pd.read_csv(PHASE60_DIR / "strength_calibration.csv")
    assert len(c_df) == 6
    high_bucket = c_df[c_df["strength_bucket"] == "90-100"].iloc[0]
    low_bucket = c_df[c_df["strength_bucket"] == "0-30"].iloc[0]
    assert high_bucket["avg_actual_return_pct"] > low_bucket["avg_actual_return_pct"]

def test_4_model_comparison_v34_ta_veto_superiority():
    m_df = pd.read_csv(PHASE60_DIR / "model_comparison.csv")
    spread_row = m_df[m_df["metric"] == "Top - Bottom Net Spread (-20bps)"].iloc[0]
    assert float(spread_row["V3.4_TA_Veto"].replace(" bps", "").replace("+", "")) > float(spread_row["V3.2_Frozen"].replace(" bps", "").replace("+", ""))

def test_5_production_immutability_checksums_match():
    pre_file = PHASE60_DIR / "checksums_preflight.json"
    post_file = PHASE60_DIR / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
