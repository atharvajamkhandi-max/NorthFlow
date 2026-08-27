"""
research/v40_shadow/test_v40_shadow.py
Isolated research unit tests for Phase 40 True Forward Shadow Pipeline.
"""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path

PHASE40_DIR = Path(__file__).resolve().parent

def test_1_manifest_immutability():
    m_file = PHASE40_DIR / "v33_shadow_manifest.json"
    assert m_file.exists()
    with open(m_file, "r") as f:
        m = json.load(f)
    assert m["model_version"] == "MODEL_V3.3_TRUE_FORWARD_SHADOW"
    assert m["conformal_multiplier"] == 1.30

def test_2_true_forward_ledger_structure():
    l_file = PHASE40_DIR / "prospective_predictions" / "true_forward_ledger.csv"
    assert l_file.exists()
    df = pd.read_csv(l_file)
    assert len(df) > 0
    assert "prediction_hash" in df.columns
    assert "tier" in df.columns
    assert (df["tier"] == "TRUE_FORWARD_SHADOW").all()

def test_3_prediction_hash_integrity():
    l_file = PHASE40_DIR / "prospective_predictions" / "true_forward_ledger.csv"
    df = pd.read_csv(l_file)
    sample_row = df.iloc[0]
    assert len(sample_row["prediction_hash"]) == 64

def test_4_failure_ledger_exists():
    f_file = PHASE40_DIR / "prospective_predictions" / "true_forward_failures.csv"
    assert f_file.exists()
    df = pd.read_csv(f_file)
    assert len(df) > 0
    assert "abs_error" in df.columns
    assert "breach_type" in df.columns

def test_5_cutover_gates_integrity():
    m_file = PHASE40_DIR / "shadow_metrics.json"
    assert m_file.exists()
    with open(m_file, "r") as f:
        m = json.load(f)
    assert m["accuracy_gain_pp"] >= 5.0
    assert m["p10_p90_coverage"] >= 70.0
    assert m["gates_evaluation"]["gate_13_zero_lookahead_violations"] is True
