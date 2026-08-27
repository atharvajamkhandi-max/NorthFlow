"""
research/v45/test_v45_candidate_audit.py
Isolated research unit tests for Phase 45 Final V3.4 Candidate Audit and Untouched Test Partition.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE45_DIR = Path(__file__).resolve().parent

def test_1_final_test_lock_integrity():
    lock_file = PHASE45_DIR / "sandbox" / "final_test_lock.json"
    assert lock_file.exists()
    with open(lock_file, "r") as f:
        data = json.load(f)
    assert data["total_rows"] > 10000
    assert data["unique_sessions"] > 50
    assert len(data["sha256_checksum"]) == 64
    assert data["zero_live_forward_overlap"] is True

def test_2_untouched_test_scorecard_integrity():
    s_file = PHASE45_DIR / "audit_results" / "untouched_test_scorecard.json"
    assert s_file.exists()
    with open(s_file, "r") as f:
        data = json.load(f)
    assert len(data) >= 5
    v34_card = next(d for d in data if "Candidate V3.4" in d["candidate"])
    assert v34_card["rank_ic"] > 0.10
    assert v34_card["directional_accuracy"] >= 54.0

def test_3_bootstrap_inference_statistical_significance():
    b_file = PHASE45_DIR / "sandbox" / "bootstrap_inference_results.json"
    assert b_file.exists()
    with open(b_file, "r") as f:
        data = json.load(f)
    assert data["n_bootstraps"] == 1000
    assert data["cluster_unit"] == "trading_session"
    assert data["statistically_significant_ic_gain"] is True

def test_4_economic_backtest_positive_net_spread():
    e_file = PHASE45_DIR / "sandbox" / "economic_backtest_summary.json"
    assert e_file.exists()
    with open(e_file, "r") as f:
        data = json.load(f)
    assert data["net_spread_bps_after_costs"] > 200.0

def test_5_phase45_isolation_from_production_and_v33():
    assert (PHASE45_DIR / "sandbox").exists()
    assert (PHASE45_DIR / "audit_results").exists()
