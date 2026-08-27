"""
research/v39_shadow/test_v39_shadow.py
Isolated research unit tests for Phase 39 Prospective Shadow Pipeline.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

PHASE39_DIR = Path(__file__).resolve().parent

def test_1_manifest_exists_and_frozen():
    manifest_file = PHASE39_DIR / "shadow_manifest.json"
    assert manifest_file.exists()
    import json
    with open(manifest_file, "r") as f:
        data = json.load(f)
    assert data["model_version"] == "MODEL_V3.3_SHADOW"
    assert data["conformal_multiplier"] == 1.30

def test_2_shadow_prediction_immutability():
    preds_file = PHASE39_DIR / "shadow_predictions.csv"
    assert preds_file.exists()
    df = pd.read_csv(preds_file)
    assert len(df) > 0
    assert "prediction_id" in df.columns
    assert "v33_exp_20d" in df.columns
    assert "v33_p10_20d" in df.columns
    assert "v33_p90_20d" in df.columns

def test_3_matured_outcomes_integrity():
    outcomes_file = PHASE39_DIR / "shadow_outcomes.csv"
    assert outcomes_file.exists()
    df = pd.read_csv(outcomes_file)
    assert len(df) > 0
    assert "v33_dir_correct" in df.columns
    assert "v33_in_p10_p90" in df.columns

def test_4_conformal_interval_containment_rate():
    metrics_file = PHASE39_DIR / "shadow_metrics.json"
    assert metrics_file.exists()
    import json
    with open(metrics_file, "r") as f:
        data = json.load(f)
    assert data["p10_p90_coverage"] >= 70.0
    assert data["accuracy_gain_pp"] >= 5.0
