"""
research/v53/test_v53_tradingagents_audit.py
Isolated unit tests for Phase 53 TradingAgents India Compatibility & Integration Audit.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE53_DIR = Path(__file__).resolve().parent

def test_1_upstream_metadata_and_india_audit_exist():
    u_file = PHASE53_DIR / "audit_results" / "upstream_metadata.json"
    i_file = PHASE53_DIR / "audit_results" / "india_data_audit.csv"
    assert u_file.exists()
    assert i_file.exists()
    df_i = pd.read_csv(i_file)
    assert len(df_i) == 22
    assert "status" in df_i.columns

def test_2_anti_leakage_10_vectors_caught():
    l_file = PHASE53_DIR / "audit_results" / "anti_leakage_attack_results.json"
    assert l_file.exists()
    with open(l_file, "r") as f:
        data = json.load(f)
    assert len(data) == 11
    for k, v in data.items():
        if k != "clean_baseline_check":
            assert v["status"] == "CAUGHT_AND_BLOCKED"
    assert data["clean_baseline_check"]["status"] == "CLEAN_0_LEAKAGE"

def test_3_quant_vs_tradingagents_comparison_v34_superiority():
    c_file = PHASE53_DIR / "audit_results" / "quant_vs_tradingagents_comparison.csv"
    assert c_file.exists()
    df = pd.read_csv(c_file)
    acc_row = df[df["metric"].str.contains("Accuracy")].iloc[0]
    mae_row = df[df["metric"].str.contains("MAE")].iloc[0]
    assert acc_row["v34_hybrid"] > acc_row["tradingagents"]
    assert mae_row["v34_hybrid"] < mae_row["tradingagents"]

def test_4_role_evaluation_categorizes_12_roles():
    r_file = PHASE53_DIR / "audit_results" / "tradingagents_role_evaluation.csv"
    assert r_file.exists()
    df = pd.read_csv(r_file)
    assert len(df) == 12
    # Verify return forecasting is unsuitable while risk/explanation is suitable
    ret_role = df[df["role"].str.contains("Return Forecasting")].iloc[0]
    exp_role = df[df["role"].str.contains("Explaining")].iloc[0]
    assert ret_role["suitability"] == "UNSUITABLE"
    assert exp_role["suitability"] == "HIGHLY SUITABLE"

def test_5_evidence_router_config_governance_verdict():
    g_file = PHASE53_DIR / "audit_results" / "evidence_router_config.json"
    assert g_file.exists()
    with open(g_file, "r") as f:
        data = json.load(f)
    assert data["governance_verdict"].startswith("B. INTEGRATE ONLY AS QUALITATIVE EVIDENCE")
    assert data["empirical_weights"]["v34_primary_quant_forecast"] >= 70.0
