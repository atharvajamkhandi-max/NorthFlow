"""
research/v62_reconciliation/tests/test_v62_1_reconciliation.py
Isolated unit tests for Phase 62.1 Live Shadow Ledger Reconciliation and Accounting Audit.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

V62_DIR = Path(__file__).resolve().parent.parent.parent / "v62"
RECON_DIR = Path(__file__).resolve().parent.parent

def test_1_reconciliation_summary_and_scorecard_exist():
    r_file = RECON_DIR / "reconciliation_summary.csv"
    s_file = V62_DIR / "scorecards" / "daily_model_scorecard.csv"
    assert r_file.exists()
    assert s_file.exists()
    df_r = pd.read_csv(r_file)
    df_s = pd.read_csv(s_file)
    assert len(df_r) == 4
    assert len(df_s) == 4
    # Reconciled: 2026-08-24 has exactly 299 predictions and 299 matured 1D observations
    assert df_r.loc[df_r["session_date"] == "2026-08-24", "raw_predictions"].iloc[0] == 299
    assert df_r.loc[df_r["session_date"] == "2026-08-24", "matured_1D"].iloc[0] == 299
    assert df_s.loc[df_s["session_date"] == "2026-08-24", "matured_obs_1D"].iloc[0] == 299

def test_2_model_comparability_identical_universe():
    m_file = RECON_DIR / "model_comparability_audit.csv"
    assert m_file.exists()
    df_m = pd.read_csv(m_file)
    assert len(df_m) == 3
    assert (df_m["unique_count"] == 0).all()
    assert (df_m["status"] == "100%_ALIGNED").all()

def test_3_hash_immutability_100_percent():
    h_file = RECON_DIR / "hash_integrity_audit.json"
    assert h_file.exists()
    with open(h_file, "r") as f:
        data = json.load(f)
    assert data["hash_mismatches_count"] == 0
    assert data["immutability_guarantee"] == "100% BIT-EXACT & UNMODIFIED"

def test_4_horizon_logic_correct():
    h_file = RECON_DIR / "horizon_maturation_audit.csv"
    assert h_file.exists()
    df_h = pd.read_csv(h_file)
    assert len(df_h) == 4
    assert (df_h["calendar_independent"] == True).all()

def test_5_production_immutability_checksums_match():
    pre_file = RECON_DIR / "checksums_preflight.json"
    post_file = RECON_DIR / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
