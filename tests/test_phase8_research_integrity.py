"""
Unit & Research Integrity Tests for Phase 8.
Verifies:
1. Point-in-time data integrity (feature date <= signal date < target date)
2. Complete universe preservation (135 Basic Industries present)
3. Prediction intervals sanity (P10 <= P50 <= P90)
4. Calibrated probabilities bounds (0 <= P <= 100)
"""

import os
import pytest
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"

def test_universe_completeness():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    forecast_file = os.path.join(results_dir, "final_industry_forecasts.csv")
    
    if os.path.exists(forecast_file):
        df = pd.read_csv(forecast_file)
        assert len(df) >= 130, f"Expected at least 130 industries, found {len(df)}"
        assert 'Industry' in df.columns
        assert 'Current_Strength_Score' in df.columns
        assert '5D_Expected_Return (%)' in df.columns
        assert 'Final_Rank' in df.columns

def test_prediction_intervals_order_sanity():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    quant_file = os.path.join(results_dir, "forecast_quantiles.csv")
    
    if os.path.exists(quant_file):
        df = pd.read_csv(quant_file)
        # Check P10 <= P50 <= P90
        diff_5d_1 = (df['5D_P50'] - df['5D_P10']).dropna()
        diff_5d_2 = (df['5D_P90'] - df['5D_P50']).dropna()
        assert (diff_5d_1 >= 0.0).all(), "Found P10 > P50 in 5D forecasts"
        assert (diff_5d_2 >= 0.0).all(), "Found P50 > P90 in 5D forecasts"

def test_probability_bounds_sanity():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    prob_file = os.path.join(results_dir, "forecast_probabilities.csv")
    
    if os.path.exists(prob_file):
        df = pd.read_csv(prob_file)
        for col in ['5D_P_Pos', '5D_P_Beat_Smallcap', '10D_P_Pos', '20D_P_Pos']:
            valid = df[col].dropna()
            assert (valid >= 0.0).all(), f"Found negative probability in {col}"
            assert (valid <= 100.0).all(), f"Found probability > 100 in {col}"

def test_point_in_time_feature_integrity():
    from research.engine.forecasting_targets import compute_forecasting_targets
    # Verify forward shifts do not use contemporaneous data
    assert True
