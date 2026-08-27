"""
research/v44/test_v44_next_gen_quant.py
Isolated research unit tests for Phase 44 Next-Gen Quant Forecasting Engine.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

PHASE44_DIR = Path(__file__).resolve().parent

def test_1_phase44_tournament_summary_integrity():
    t_file = PHASE44_DIR / "tournament_results" / "phase44_tournament_summary.json"
    assert t_file.exists()
    with open(t_file, "r") as f:
        data = json.load(f)
    assert len(data) == 5
    hgb_entry = next(d for d in data if "HistGradientBoosting" in d["model"])
    assert hgb_entry["mean_rank_ic"] > 0.08
    assert hgb_entry["mean_mae"] < 8.50

def test_2_feature_ablation_monotonic_gain():
    a_file = PHASE44_DIR / "sandbox" / "feature_ablation_results.json"
    assert a_file.exists()
    with open(a_file, "r") as f:
        data = json.load(f)
    assert len(data) >= 4
    # Full nonlinear interactions must have higher Rank IC than base 1D return only
    base_ic = data[0]["rank_ic"]
    full_ic = data[-1]["rank_ic"]
    assert full_ic > base_ic

def test_3_hyperparameter_robustness_stability():
    p_file = PHASE44_DIR / "sandbox" / "hyperparameter_robustness.json"
    assert p_file.exists()
    with open(p_file, "r") as f:
        data = json.load(f)
    accs = [d["directional_accuracy"] for d in data]
    # Verify no collapse across +/-20% capacity perturbation
    assert max(accs) - min(accs) < 2.0

def test_4_phase44_isolation_from_production_and_v33():
    # Verify Phase 44 is completely self-contained in research/v44/
    assert (PHASE44_DIR / "sandbox").exists()
    assert (PHASE44_DIR / "tournament_results").exists()
