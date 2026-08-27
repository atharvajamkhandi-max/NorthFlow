"""
Unit & Research Integrity Tests for Phase 10 Advanced Industry Alpha Engine.
Verifies:
1. Non-Gaussian quantile ordering (P5 <= P10 <= P25 <= P50 <= P75 <= P90 <= P95)
2. High-upside probability monotonicity
3. Extreme upside signature scoring bounds
4. Prospective ledger immutability and schema integrity
"""

import os
import pytest
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"

def test_phase10_quantile_ordering():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    dist_file = os.path.join(results_dir, "phase10_return_distributions.csv")
    
    if os.path.exists(dist_file):
        df = pd.read_csv(dist_file)
        assert ((df['P10'] - df['P5']).dropna() >= -1e-5).all(), "Found P5 > P10"
        assert ((df['P25'] - df['P10']).dropna() >= -1e-5).all(), "Found P10 > P25"
        assert ((df['P50'] - df['P25']).dropna() >= -1e-5).all(), "Found P25 > P50"
        assert ((df['P75'] - df['P50']).dropna() >= -1e-5).all(), "Found P50 > P75"
        assert ((df['P90'] - df['P75']).dropna() >= -1e-5).all(), "Found P75 > P90"
        assert ((df['P95'] - df['P90']).dropna() >= -1e-5).all(), "Found P90 > P95"

def test_phase10_threshold_monotonicity():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    prob_file = os.path.join(results_dir, "phase10_threshold_probabilities.csv")
    
    if os.path.exists(prob_file):
        df = pd.read_csv(prob_file)
        diff1 = (df['20D_P_gt_2pct'] - df['20D_P_gt_5pct']).dropna()
        diff2 = (df['20D_P_gt_5pct'] - df['20D_P_gt_8pct']).dropna()
        diff3 = (df['20D_P_gt_8pct'] - df['20D_P_gt_10pct']).dropna()
        diff4 = (df['20D_P_gt_10pct'] - df['20D_P_gt_15pct']).dropna()
        diff5 = (df['20D_P_gt_15pct'] - df['20D_P_gt_20pct']).dropna()
        assert (diff1 >= -1e-5).all(), "Monotonicity violation between P(>2%) and P(>5%)"
        assert (diff2 >= -1e-5).all(), "Monotonicity violation between P(>5%) and P(>8%)"
        assert (diff3 >= -1e-5).all(), "Monotonicity violation between P(>8%) and P(>10%)"
        assert (diff4 >= -1e-5).all(), "Monotonicity violation between P(>10%) and P(>15%)"
        assert (diff5 >= -1e-5).all(), "Monotonicity violation between P(>15%) and P(>20%)"

def test_phase10_extreme_upside_scoring_bounds():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    up_file = os.path.join(results_dir, "phase10_extreme_upside.csv")
    
    if os.path.exists(up_file):
        df = pd.read_csv(up_file)
        valid = df['Extreme_Upside_Score'].dropna()
        assert (valid >= 0.0).all()
        assert (valid <= 100.0).all()

def test_phase10_prospective_ledger_integrity():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    led_file = os.path.join(results_dir, "phase10_prospective_ledger.csv")
    
    if os.path.exists(led_file):
        df = pd.read_csv(led_file)
        assert len(df) >= 130
        assert 'is_frozen' in df.columns
        assert (df['is_frozen'] == 1).all()
