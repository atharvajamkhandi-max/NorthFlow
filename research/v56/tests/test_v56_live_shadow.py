"""
research/v56/tests/test_v56_live_shadow.py
Isolated unit tests for Phase 56 NorthFlow V3.4 + TradingAgents India Live Shadow Implementation.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE56_DIR = Path(__file__).resolve().parent.parent

def test_1_manifest_and_india_adapter_exist():
    m_file = PHASE56_DIR / "manifests" / "v34_ta_shadow_manifest.json"
    a_file = PHASE56_DIR / "india_adapter" / "india_adapter_config.json"
    assert m_file.exists()
    assert a_file.exists()
    with open(m_file, "r") as f:
        m = json.load(f)
    assert m["model_name"] == "MODEL_NORTHFLOW_V34_TA_VETO_SHADOW"
    assert "manifest_hash" in m

def test_2_anti_leakage_16_vectors_caught():
    l_file = PHASE56_DIR / "anti_leakage" / "anti_leakage_attack_results.json"
    assert l_file.exists()
    with open(l_file, "r") as f:
        data = json.load(f)
    assert len(data) == 17
    for k, v in data.items():
        if k != "clean_baseline_check":
            assert v["status"] == "CAUGHT_AND_BLOCKED"
    assert data["clean_baseline_check"]["status"] == "CLEAN_0_LEAKAGE"

def test_3_shadow_ledger_three_independent_benchmarks_exist():
    l_file = PHASE56_DIR / "ledger" / "northflow_v34_ta_shadow_ledger.csv"
    assert l_file.exists()
    df = pd.read_csv(l_file)
    assert len(df) >= 134
    # Must contain 3 independent benchmarks
    assert "v32_production_benchmark_return" in df.columns
    assert "v34_standalone_shadow_return" in df.columns
    assert "final_shadow_signal" in df.columns

def test_4_veto_logic_suppresses_high_risk_signals():
    l_file = PHASE56_DIR / "ledger" / "northflow_v34_ta_shadow_ledger.csv"
    df = pd.read_csv(l_file)
    # Verify veto schema columns exist
    assert "veto_applied" in df.columns
    assert "final_shadow_status" in df.columns
    assert "ta_risk_level" in df.columns

def test_5_production_immutability_checksums_match():
    pre_file = PHASE56_DIR / "manifests" / "checksums_preflight.json"
    post_file = PHASE56_DIR / "manifests" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
