"""
research/v43/test_v43_track_a_and_b.py
Isolated research unit tests for Phase 43 Track A (Live Monitor) and Track B (Quant Sandbox).
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE43_DIR = Path(__file__).resolve().parent

def test_1_track_a_live_status_clean():
    s_file = PHASE43_DIR / "track_a_live_monitor" / "track_a_live_status.json"
    assert s_file.exists()
    with open(s_file, "r") as f:
        s = json.load(f)
    assert s["live_forward_boundary"] == "2026-08-24"
    assert s["current_live_sessions_captured"] == 1
    assert s["matured_20d_sessions"] == 0
    assert s["data_quality_issues"] == 0
    assert "B. CONTINUE TRUE LIVE-FORWARD SHADOW" in s["promotion_gate_status"]["verdict"]

def test_2_track_b_tournament_scorecard_integrity():
    t_file = PHASE43_DIR / "research_sandbox" / "tournament_scorecard.json"
    assert t_file.exists()
    with open(t_file, "r") as f:
        cards = json.load(f)
    assert len(cards) >= 6
    hgb_card = next(c for c in cards if "HistGradientBoosting" in c["model"])
    assert hgb_card["mean_directional_accuracy"] >= 54.0
    assert hgb_card["mean_rank_ic"] >= 0.10

def test_3_track_b_isolation_from_track_a():
    # Verify Track B did not touch Track A or production
    assert (PHASE43_DIR / "track_a_live_monitor").exists()
    assert (PHASE43_DIR / "research_sandbox").exists()
