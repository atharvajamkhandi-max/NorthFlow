"""
research/v59/tests/test_v59_data_bus.py
Isolated unit tests for Phase 59 NorthFlow India Data Bus Implementation.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE59_DIR = Path(__file__).resolve().parent.parent

def test_1_verification_matrix_and_health_exist():
    v_file = PHASE59_DIR / "source_verification_matrix.csv"
    h_file = PHASE59_DIR / "data_bus_health.json"
    assert v_file.exists()
    assert h_file.exists()
    df_v = pd.read_csv(v_file)
    assert len(df_v) == 10
    with open(h_file, "r") as f:
        h = json.load(f)
    assert h["bus_name"] == "NORTHFLOW_INDIA_DATA_BUS"
    assert h["operating_environment"] == "SHADOW_RESEARCH_ONLY"

def test_2_anti_leakage_16_vectors_caught():
    l_file = PHASE59_DIR / "anti_leakage_results.json"
    assert l_file.exists()
    with open(l_file, "r") as f:
        data = json.load(f)
    assert len(data) == 17
    for k, v in data.items():
        if k != "clean_baseline_check":
            assert v["status"] == "CAUGHT_AND_BLOCKED"
    assert data["clean_baseline_check"]["status"] == "CLEAN_0_LEAKAGE"

def test_3_failure_injection_16_scenarios_handled():
    f_file = PHASE59_DIR / "failure_injection_results.json"
    assert f_file.exists()
    with open(f_file, "r") as f:
        data = json.load(f)
    assert len(data) == 16
    for k, v in data.items():
        assert "result" in v

def test_4_pit_validation_100_percent_compliant():
    p_file = PHASE59_DIR / "pit_validation_report.json"
    assert p_file.exists()
    with open(p_file, "r") as f:
        data = json.load(f)
    assert data["prediction_cutoff_ist"] == "08:30:00 IST"
    assert data["pit_blocked_count"] == 0

def test_5_production_immutability_checksums_match():
    pre_file = PHASE59_DIR / "anti_leakage" / "checksums_preflight.json"
    post_file = PHASE59_DIR / "anti_leakage" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
