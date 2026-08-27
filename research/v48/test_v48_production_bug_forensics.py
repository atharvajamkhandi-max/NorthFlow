"""
research/v48/test_v48_production_bug_forensics.py
Isolated regression test suite for Phase 48 Production Bug Forensics & V3.2 Output Validation.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE48_DIR = Path(__file__).resolve().parent

def test_1_source_vs_ui_reconciliation_zero_mismatches():
    r_file = PHASE48_DIR / "audit_results" / "source_vs_ui_reconciliation.json"
    assert r_file.exists()
    with open(r_file, "r") as f:
        records = json.load(f)
    assert len(records) > 200
    for r in records:
        assert abs(r["canonical_strength"] - r["ui_strength"]) < 1e-4
        assert abs(r["canonical_20d_ret_pct"] - r["ui_20d_ret_pct"]) < 1e-4
        assert r["canonical_rating"] == r["ui_rating"]
        assert abs(r["target_price"] - (1000.0 * (1.0 + r["canonical_20d_ret_pct"] / 100.0))) < 0.05

def test_2_stock_projection_monotonicity():
    s_file = PHASE48_DIR / "audit_results" / "stock_projection_audit.json"
    assert s_file.exists()
    with open(s_file, "r") as f:
        records = json.load(f)
    assert len(records) >= 3
    for r in records:
        assert r["p10_price"] <= r["p50_price"] <= r["p90_price"]
        assert r["p10_ret"] <= r["p50_ret"] <= r["p90_ret"]

def test_3_preflight_checksums_match():
    p_file = PHASE48_DIR / "audit_results" / "preflight_checksums.json"
    assert p_file.exists()
    with open(p_file, "r") as f:
        data = json.load(f)
    assert len(data["final_predictions_csv"]) == 64
    assert len(data["decision_ledger_db"]) == 64

def test_4_bug_reproduction_document_exists():
    assert (PHASE48_DIR / "BUG_REPRODUCTION.md").exists()
    assert (PHASE48_DIR / "PRODUCTION_E2E_VALIDATION.md").exists()
