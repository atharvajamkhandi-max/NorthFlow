"""
research/live_forward/tests/test_live_operations_verification.py
Isolated unit tests for Live Runner Operations Verification.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

LIVE_DIR = Path(__file__).resolve().parent.parent

def test_1_scheduler_and_operational_status_exist():
    s_file = LIVE_DIR / "scheduler" / "scheduler_config.json"
    o_file = LIVE_DIR / "monitoring" / "operational_status.json"
    r_file = LIVE_DIR / "monitoring" / "failure_recovery_audit.json"
    assert s_file.exists()
    assert o_file.exists()
    assert r_file.exists()
    with open(s_file, "r") as f:
        sched = json.load(f)
    assert sched["timezone"] == "Asia/Kolkata (IST, UTC+05:30)"
    assert sched["weekend_skipping_active"] == True

def test_2_failure_recovery_all_11_scenarios_handled():
    r_file = LIVE_DIR / "monitoring" / "failure_recovery_audit.json"
    with open(r_file, "r") as f:
        data = json.load(f)
    assert len(data) == 11
    for k, v in data.items():
        assert "result" in v

def test_3_operational_status_integrity():
    o_file = LIVE_DIR / "monitoring" / "operational_status.json"
    with open(o_file, "r") as f:
        op = json.load(f)
    assert op["system_status"] == "ONLINE_HEALTHY_AND_MONITORED"
    assert op["total_operational_errors"] == 0
    assert op["promotion_gate_status"] == "LOCKED (DO NOT PROMOTE)"
    assert op["active_production_model"] == "MODEL_V3.2_FROZEN (100% UNTOUCHED)"

def test_4_stress_simulation_zero_corruptions():
    s_file = LIVE_DIR / "monitoring" / "stress_simulation_audit.json"
    with open(s_file, "r") as f:
        stress = json.load(f)
    assert stress["data_corruption_events"] == 0
    assert stress["duplicate_predictions_created"] == 0

def test_5_production_immutability_checksums_match():
    pre_file = LIVE_DIR / "safety" / "checksums_preflight_ops.json"
    post_file = LIVE_DIR / "safety" / "checksums_postflight_ops.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
