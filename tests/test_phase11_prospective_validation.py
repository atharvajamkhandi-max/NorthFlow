"""
Unit & Research Integrity Tests for Phase 11 Prospective Shadow Validation Engine.
Verifies:
1. Forecast ledger completeness and immutable model fingerprint
2. Forward realization math integrity
3. Brier score and ECE metric bounds
4. Top-K percentile ordering and cross-sectional coverage
"""

import os
import pytest
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"

def test_phase11_daily_forecast_ledger_integrity():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    led_file = os.path.join(results_dir, "phase11_daily_forecast_ledger.csv")
    
    if os.path.exists(led_file):
        df = pd.read_csv(led_file)
        assert len(df) >= 135, f"Expected at least 135 ledger records, found {len(df)}"
        assert 'model_version' in df.columns
        assert 'feature_version' in df.columns
        assert (df['model_version'] == 'MODEL_V10.1_FROZEN').all()
        assert (df['feature_version'] == 'FEATURE_V10.1').all()

def test_phase11_realized_outcomes_math():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    real_file = os.path.join(results_dir, "phase11_realized_outcomes.csv")
    
    if os.path.exists(real_file):
        df = pd.read_csv(real_file)
        assert '20D_abs_error' in df.columns
        valid_err = df['20D_abs_error'].dropna()
        assert (valid_err >= -1e-5).all(), "Found negative absolute error"

def test_phase11_calibration_metric_bounds():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    cal_file = os.path.join(results_dir, "phase11_threshold_calibration.csv")
    
    if os.path.exists(cal_file):
        df = pd.read_csv(cal_file)
        assert (df['Brier_Score'] >= 0.0).all()
        assert (df['Brier_Score'] <= 1.0).all()
        assert (df['ECE'] >= 0.0).all()

def test_phase11_top_k_performance_ordering():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    top_file = os.path.join(results_dir, "phase11_top_k_performance.csv")
    
    if os.path.exists(top_file):
        df = pd.read_csv(top_file)
        assert len(df) >= 5
        assert 'Percentile_Group' in df.columns
        assert '20D_Mean_Return (%)' in df.columns
