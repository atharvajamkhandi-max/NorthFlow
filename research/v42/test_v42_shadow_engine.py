"""
research/v42/test_v42_shadow_engine.py
Isolated research unit tests for Phase 42 True Live-Forward Shadow Automation Engine.
"""
import pytest
import pandas as pd
import json
from pathlib import Path

PHASE42_DIR = Path(__file__).resolve().parent

def test_1_session_resolution_exists():
    s_file = PHASE42_DIR / "session_resolution.json"
    assert s_file.exists()
    with open(s_file, "r") as f:
        s = json.load(f)
    assert s["true_live_forward_boundary"] == "2026-08-24"

def test_2_model_manifest_immutability():
    m_file = PHASE42_DIR / "v33_shadow_manifest.json"
    assert m_file.exists()
    with open(m_file, "r") as f:
        m = json.load(f)
    assert m["model_version"] == "MODEL_V3.3_LIVE_FORWARD_FROZEN"
    assert m["online_learning_prohibited"] is True
    assert len(m["manifest_hash"]) == 64

def test_3_first_live_snapshot_integrity():
    snap_file = PHASE42_DIR / "live_forward" / "2026-08-24" / "predictions.csv"
    assert snap_file.exists()
    df = pd.read_csv(snap_file)
    assert len(df) > 0
    assert "prediction_hash" in df.columns
    assert "feature_snapshot_hash" in df.columns
    assert (df["tier"] == "TRUE_LIVE_FORWARD_SHADOW").all()

def test_4_universe_exact_matching():
    m_file = PHASE42_DIR / "live_forward" / "2026-08-24" / "manifest.json"
    assert m_file.exists()
    with open(m_file, "r") as f:
        m = json.load(f)
    assert m["v32_universe_count"] == m["v33_universe_count"]
    assert m["universe_mismatches"] == 0

def test_5_promotion_gate_decision_continue_shadow():
    g_file = PHASE42_DIR / "promotion_gate_evaluation.json"
    assert g_file.exists()
    with open(g_file, "r") as f:
        g = json.load(f)
    assert g["mandatory_final_decision"] == "B. CONTINUE TRUE LIVE-FORWARD SHADOW"
