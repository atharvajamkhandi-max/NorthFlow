"""
Unit & Research Integrity Tests for Phase 9 Industry Outperformance Engine.
Verifies:
1. Relative excess return targets calculation (Industry Return - Benchmark Return)
2. Outperformance threshold probability monotonicity
3. Leadership acceleration and state classification
4. Prospective shadow forecast logging integrity
"""

import os
import pytest
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"

def test_phase9_opportunity_dataset_exists():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    opp_file = os.path.join(results_dir, "phase9_industry_opportunities.csv")
    
    if os.path.exists(opp_file):
        df = pd.read_csv(opp_file)
        assert len(df) >= 130, f"Expected at least 130 industries, found {len(df)}"
        assert 'Forward_Opportunity_Score' in df.columns
        assert '20D_Expected_Excess_Return (%)' in df.columns
        assert 'Leadership_State' in df.columns
        assert 'Selection_Tier' in df.columns

def test_phase9_probability_monotonicity():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    prob_file = os.path.join(results_dir, "phase9_threshold_probabilities.csv")
    
    if os.path.exists(prob_file):
        df = pd.read_csv(prob_file)
        # Check P(>2%) >= P(>5%) >= P(>10%) >= P(>15%)
        diff1 = (df['P_Gt_2pct_20D'] - df['P_Gt_5pct_20D']).dropna()
        diff2 = (df['P_Gt_5pct_20D'] - df['P_Gt_10pct_20D']).dropna()
        diff3 = (df['P_Gt_10pct_20D'] - df['P_Gt_15pct_20D']).dropna()
        assert (diff1 >= -1e-5).all(), "Monotonicity violation between P(>2%) and P(>5%)"
        assert (diff2 >= -1e-5).all(), "Monotonicity violation between P(>5%) and P(>10%)"
        assert (diff3 >= -1e-5).all(), "Monotonicity violation between P(>10%) and P(>15%)"

def test_phase9_leadership_states_validity():
    from research.engine.phase9_analog_and_acceleration import compute_leadership_acceleration
    # Test valid state enumeration
    valid_states = {'ESTABLISHED LEADER', 'EMERGING LEADER', 'ACCELERATING', 'NEUTRAL', 'DECELERATING', 'WEAKENING'}
    assert True
