"""
research/v58/tests/test_v58_data_source_audit.py
Isolated unit tests for Phase 58 Indian Market Data Source & PIT Audit.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE58_DIR = Path(__file__).resolve().parent.parent

def test_1_source_inventory_and_hierarchy_exist():
    i_file = PHASE58_DIR / "source_inventory" / "current_data_source_inventory.csv"
    h_file = PHASE58_DIR / "source_ranking" / "indian_data_source_hierarchy.csv"
    assert i_file.exists()
    assert h_file.exists()
    df_i = pd.read_csv(i_file)
    df_h = pd.read_csv(h_file)
    assert len(df_i) >= 15
    assert len(df_h) >= 7

def test_2_anti_leakage_16_vectors_caught():
    l_file = PHASE58_DIR / "anti_leakage" / "anti_leakage_attack_results.json"
    assert l_file.exists()
    with open(l_file, "r") as f:
        data = json.load(f)
    assert len(data) == 17
    for k, v in data.items():
        if k != "clean_baseline_check":
            assert v["status"] == "CAUGHT_AND_BLOCKED"
    assert data["clean_baseline_check"]["status"] == "CLEAN_0_LEAKAGE"

def test_3_pit_rules_specify_0830_ist_cutoff():
    p_file = PHASE58_DIR / "pit_audit" / "pit_provenance_rules.json"
    assert p_file.exists()
    with open(p_file, "r") as f:
        data = json.load(f)
    assert data["prediction_cutoff_ist"] == "08:30:00 IST"
    assert data["verified_point_in_time_coverage_pct"] == 100.0

def test_4_data_bus_design_specifies_no_override():
    b_file = PHASE58_DIR / "data_bus_design" / "northflow_data_bus_blueprint.json"
    assert b_file.exists()
    with open(b_file, "r") as f:
        data = json.load(f)
    assert "NO_OVERRIDE" in data["design_rules"]
    assert len(data["architecture_layers"]) == 5

def test_5_production_immutability_checksums_match():
    pre_file = PHASE58_DIR / "anti_leakage" / "checksums_preflight.json"
    post_file = PHASE58_DIR / "anti_leakage" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
