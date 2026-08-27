"""
research/v41/test_v41_provenance.py
Isolated research unit tests for Phase 41 Forensic Provenance & Evidence Separation.
"""
import pytest
import pandas as pd
import json
from pathlib import Path

PHASE41_DIR = Path(__file__).resolve().parent

def test_1_timeline_matrix_exists_and_classifies_tiers():
    t_file = PHASE41_DIR / "timeline_provenance_matrix.json"
    assert t_file.exists()
    with open(t_file, "r") as f:
        t = json.load(f)
    assert "tier_1_historical_training" in t
    assert "tier_3_historical_holdout" in t
    assert "tier_5_true_live_forward" in t
    assert t["tier_3_historical_holdout"]["classification"] == "HISTORICAL_OUT_OF_SAMPLE_HOLDOUT"
    assert t["tier_5_true_live_forward"]["classification"] == "TRUE_LIVE_FORWARD_SHADOW"

def test_2_live_forward_manifest_frozen():
    m_file = PHASE41_DIR / "v33_live_forward_manifest.json"
    assert m_file.exists()
    with open(m_file, "r") as f:
        m = json.load(f)
    assert m["model_version"] == "MODEL_V3.3_LIVE_FORWARD_SHADOW"
    assert m["conformal_multiplier"] == 1.30
    assert m["true_live_forward_start_date"] == "2026-08-24"

def test_3_live_forward_ledger_clean_and_unpolluted():
    l_file = PHASE41_DIR / "live_forward" / "live_forward_ledger.csv"
    assert l_file.exists()
    df = pd.read_csv(l_file)
    assert len(df) == 0  # Clean, unbackfilled prospective ledger
    assert "prediction_hash" in df.columns
    assert "model_manifest_hash" in df.columns

def test_4_historical_holdout_metrics_preserved():
    h_file = PHASE41_DIR / "historical_holdout_evidence.json"
    assert h_file.exists()
    with open(h_file, "r") as f:
        h = json.load(f)
    assert h["v33_accuracy"] == 67.48
    assert h["accuracy_gain_pp"] == 10.79
    assert h["p10_p90_coverage"] == 80.28

def test_5_final_mandatory_decision_is_continue_shadow():
    s_file = PHASE41_DIR / "phase41_summary.json"
    assert s_file.exists()
    with open(s_file, "r") as f:
        s = json.load(f)
    assert "B. CONTINUE TRUE LIVE-FORWARD SHADOW" in s["mandatory_final_decision"]
