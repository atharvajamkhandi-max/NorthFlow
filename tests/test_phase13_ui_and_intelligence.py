"""
Unit & Integration Tests for Phase 13 Production Industry Intelligence UI & Data Bridge.
Verifies:
1. Production Data Loading and Schema Completeness
2. N >= 5 Primary Universe Hard Filter in Production Datasets
3. N < 5 Research-Only Tagging and Completeness (Total == 135)
4. Industry -> Stock Bridge Schema Integrity
5. Calibrated Tail Probability Monotonicity
"""

import os
import pytest
import pandas as pd
import numpy as np

from dashboard.phase13_intelligence_terminal import load_phase12_production_data

def test_phase13_production_data_loading():
    df_primary, df_research, df_dist, df_prob, df_stock, df_ledger, df_realized, df_calib = load_phase12_production_data()
    
    assert not df_primary.empty, "Primary universe dataset is empty"
    assert not df_research.empty, "Research-only dataset is empty"
    assert len(df_primary) + len(df_research) == 135, f"Expected 135 total industries, found {len(df_primary) + len(df_research)}"

def test_phase13_primary_universe_breadth_constraint():
    df_primary, _, _, _, _, _, _, _ = load_phase12_production_data()
    assert (df_primary['constituent_count'] >= 5).all(), "Found N < 5 in primary universe"
    assert (df_primary['breadth_status'] == 'PRIMARY_ELIGIBLE').all()

def test_phase13_research_only_breadth_constraint():
    _, df_research, _, _, _, _, _, _ = load_phase12_production_data()
    assert (df_research['constituent_count'] < 5).all(), "Found N >= 5 in research-only universe"
    assert (df_research['breadth_status'] == 'INSUFFICIENT_INDUSTRY_BREADTH').all()

def test_phase13_stock_bridge_schema():
    _, _, _, _, df_stock, _, _, _ = load_phase12_production_data()
    assert not df_stock.empty
    assert 'symbol' in df_stock.columns
    assert 'relative_strength' in df_stock.columns
    assert 'trend_state' in df_stock.columns
    assert 'human_due_diligence_priority' in df_stock.columns

def test_phase13_probability_monotonicity():
    df_primary, _, _, _, _, _, _, _ = load_phase12_production_data()
    diff1 = (df_primary['20D_P_gt_5'] - df_primary['20D_P_gt_8']).dropna()
    diff2 = (df_primary['20D_P_gt_8'] - df_primary['20D_P_gt_10']).dropna()
    diff3 = (df_primary['20D_P_gt_10'] - df_primary['20D_P_gt_15']).dropna()

    assert (diff1 >= -1e-5).all()
    assert (diff2 >= -1e-5).all()
    assert (diff3 >= -1e-5).all()
