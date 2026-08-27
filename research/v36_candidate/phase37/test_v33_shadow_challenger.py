"""
research/v36_candidate/phase37/test_v33_shadow_challenger.py
Isolated research unit tests for V3.3 Challenger Engine.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

PHASE37_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PHASE37_DIR))

from v33_config import V33Config
from v33_challenger_engine import V33ChallengerEngine

def test_1_v33_config_immutability_and_flags():
    cfg = V33Config()
    assert cfg.model_version == "MODEL_V3.3_CANDIDATE"
    assert cfg.use_hgb is True
    assert cfg.use_conformal is True
    assert cfg.conformal_quantile_scale == 1.30
    assert cfg.regime_60d_offsets["WEAK_BULL"] == 12.22

def test_2_point_in_time_inference():
    cfg = V33Config()
    engine = V33ChallengerEngine(cfg)
    mock_train = pd.DataFrame({
        "industry_return_1d": [0.5, -0.2, 1.1, -0.8],
        "breadth_50": [60.0, 40.0, 75.0, 30.0],
        "RISK_SCORE": [45.0, 55.0, 35.0, 65.0],
        "CONFIDENCE_SCORE": [70.0, 50.0, 80.0, 40.0],
        "future_return_20D": [2.5, -1.2, 4.0, -3.5]
    })
    engine.fit_historical_partition(mock_train)
    assert engine.is_fitted is True

    sample_row = pd.Series({
        "date": "2026-08-21",
        "basic_industry": "Software Services",
        "industry_return_1d": 0.4,
        "breadth_50": 65.0,
        "RISK_SCORE": 40.0,
        "CONFIDENCE_SCORE": 75.0,
        "EXPECTED_RETURN_20D": 2.0,
        "P10_20D": -5.0,
        "P90_20D": 9.0,
        "EXPECTED_RETURN_60D": 15.0,
        "REGIME": "WEAK_BULL",
        "FINAL_ACTION": "BUY"
    })
    pred = engine.generate_shadow_prediction(sample_row)
    assert pred["model_version"] == "MODEL_V3.3_CANDIDATE"
    assert pred["regime"] == "WEAK_BULL"
    # 60D calibrated: 15.0 - 12.22 = 2.78
    assert pred["expected_return_60d_calibrated"] == 2.78
    # P10 / P90 expanded by 1.30
    assert pred["p90_20d_calibrated"] > 9.0
    assert pred["p10_20d_calibrated"] < -5.0

def test_3_conformal_interval_ordering():
    cfg = V33Config()
    engine = V33ChallengerEngine(cfg)
    row = pd.Series({
        "date": "2026-08-21",
        "basic_industry": "Banking",
        "EXPECTED_RETURN_20D": 1.0,
        "P10_20D": -6.0,
        "P90_20D": 8.0,
        "REGIME": "SIDEWAYS"
    })
    pred = engine.generate_shadow_prediction(row)
    assert pred["p10_20d_calibrated"] < pred["expected_return_20d"] < pred["p90_20d_calibrated"]
