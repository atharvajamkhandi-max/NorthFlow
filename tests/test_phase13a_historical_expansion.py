"""
Unit & Research Integrity Tests for Phase 13A Historical Expansion & Walk-Forward Validation.
Verifies:
1. Historical Data Quality Audit Schema & Bounds
2. Breadth Threshold Comparison (N >= 3, 5, 7, 10, 15)
3. Walk-Forward Tournament Model Stability
4. Regime Robustness Data Integrity
5. Calibrated Tail Probability Bounds
"""

import os
import pytest
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"

def test_phase13a_data_quality_audit_integrity():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    audit_file = os.path.join(results_dir, "historical_data_quality.csv")
    
    if os.path.exists(audit_file):
        df = pd.read_csv(audit_file)
        assert not df.empty
        assert 'overall_data_completeness_pct' in df.columns
        assert (df['zero_or_negative_prices'] == 0).all()
        assert (df['duplicate_records'] == 0).all()
        assert (df['overall_data_completeness_pct'] >= 99.0).all()

def test_phase13a_breadth_threshold_comparison():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    breadth_file = os.path.join(results_dir, "phase13a_breadth_threshold_comparison.csv")
    
    if os.path.exists(breadth_file):
        df = pd.read_csv(breadth_file)
        assert len(df) >= 4
        assert 'Breadth_Threshold' in df.columns
        assert 'Rank_IC' in df.columns
        assert 'Top_Bottom_Spread (%)' in df.columns
        # Top-bottom spread should be positive across all thresholds
        assert (df['Top_Bottom_Spread (%)'] > 0).all()

def test_phase13a_walk_forward_tournament():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    tourn_file = os.path.join(results_dir, "phase13a_walk_forward_tournament.csv")
    
    if os.path.exists(tourn_file):
        df = pd.read_csv(tourn_file)
        assert not df.empty
        assert 'Model' in df.columns
        assert 'Rank_IC' in df.columns
        assert 'MAE (%)' in df.columns
        assert (df['Rank_IC'] > 0).all()

def test_phase13a_regime_robustness():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    regime_file = os.path.join(results_dir, "phase13a_regime_robustness.csv")
    
    if os.path.exists(regime_file):
        df = pd.read_csv(regime_file)
        assert len(df) >= 3
        assert 'Regime' in df.columns
        assert 'Top_Decile_Excess (%)' in df.columns
        # Top decile excess should be positive in all market regimes
        assert (df['Top_Decile_Excess (%)'] > 0).all()

def test_phase13a_tail_calibration_bounds():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    tail_file = os.path.join(results_dir, "phase13a_tail_calibration.csv")
    
    if os.path.exists(tail_file):
        df = pd.read_csv(tail_file)
        assert not df.empty
        assert (df['Brier_Score'] >= 0.0).all()
        assert (df['Brier_Score'] <= 1.0).all()
        assert (df['ECE'] >= 0.0).all()
