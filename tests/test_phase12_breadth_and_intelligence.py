"""
Unit & Research Integrity Tests for Phase 12 Final Industry Intelligence & Breadth Engine.
Verifies:
1. Hard Breadth Filtering (N >= 5 in Primary vs N < 5 in Research-Only)
2. Total Universe Completeness (Sum of Primary + Research-Only == 135)
3. Tail Probability Monotonicity
4. Distribution Quantile Monotonic Ordering
5. Industry -> Stock Bridge Schema Integrity
"""

import os
import pytest
import pandas as pd
import numpy as np

BASE_DIR = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow"

def test_phase12_breadth_partition_and_completeness():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    prim_file = os.path.join(results_dir, "phase12_primary_industry_rankings.csv")
    res_file = os.path.join(results_dir, "phase12_research_only_universe.csv")
    
    if os.path.exists(prim_file) and os.path.exists(res_file):
        df_prim = pd.read_csv(prim_file)
        df_res = pd.read_csv(res_file)

        # 1. Primary hard filter
        assert (df_prim['constituent_count'] >= 5).all(), "Found N < 5 in primary universe"
        assert (df_prim['breadth_status'] == 'PRIMARY_ELIGIBLE').all()

        # 2. Research-only status
        assert (df_res['constituent_count'] < 5).all(), "Found N >= 5 in research-only universe"
        assert (df_res['breadth_status'] == 'INSUFFICIENT_INDUSTRY_BREADTH').all()

        # 3. Completeness (Total == 135)
        total_industries = len(df_prim) + len(df_res)
        assert total_industries == 135, f"Expected exactly 135 total industries, found {total_industries}"

def test_phase12_calibrated_probability_monotonicity():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    prob_file = os.path.join(results_dir, "phase12_calibrated_probabilities.csv")
    
    if os.path.exists(prob_file):
        df = pd.read_csv(prob_file)
        diff1 = (df['P_gt_5pct'] - df['P_gt_8pct']).dropna()
        diff2 = (df['P_gt_8pct'] - df['P_gt_10pct']).dropna()
        diff3 = (df['P_gt_10pct'] - df['P_gt_15pct']).dropna()

        assert (diff1 >= -1e-5).all(), "Violation: P(>5%) < P(>8%)"
        assert (diff2 >= -1e-5).all(), "Violation: P(>8%) < P(>10%)"
        assert (diff3 >= -1e-5).all(), "Violation: P(>10%) < P(>15%)"

def test_phase12_quantile_monotonic_ordering():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    dist_file = os.path.join(results_dir, "phase12_return_distributions.csv")
    
    if os.path.exists(dist_file):
        df = pd.read_csv(dist_file)
        assert ((df['P25'] - df['P10']).dropna() >= -1e-5).all(), "Found P10 > P25"
        assert ((df['P50'] - df['P25']).dropna() >= -1e-5).all(), "Found P25 > P50"
        assert ((df['P75'] - df['P50']).dropna() >= -1e-5).all(), "Found P50 > P75"
        assert ((df['P90'] - df['P75']).dropna() >= -1e-5).all(), "Found P75 > P90"
        assert ((df['P95'] - df['P90']).dropna() >= -1e-5).all(), "Found P90 > P95"

def test_phase12_stock_bridge_integrity():
    results_dir = os.path.join(BASE_DIR, "research", "results")
    stk_file = os.path.join(results_dir, "phase12_stock_bridge.csv")
    
    if os.path.exists(stk_file):
        df = pd.read_csv(stk_file)
        assert len(df) >= 20, f"Expected at least 20 stock candidates, found {len(df)}"
        assert 'symbol' in df.columns
        assert 'relative_strength' in df.columns
        assert 'trend_state' in df.columns
