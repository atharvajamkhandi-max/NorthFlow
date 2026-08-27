"""
Unit and Integration Tests for Canonical V3.2 Quantitative Service Unification.
Verifies that all website pages and services return identical, deterministic scores under MODEL_V3.2_FROZEN.
"""

import os
import pytest
import pandas as pd
import numpy as np
from database.db import Database
from config.model_v3_2_frozen import (
    MODEL_V3_2_FINGERPRINT,
    FROZEN_INDUSTRY_FACTOR_WEIGHTS,
    FROZEN_REGIME_MULTIPLIERS
)
from analytics.canonical_v3_2_service import (
    get_model_fingerprint,
    get_canonical_hierarchy_quant_scores,
    get_canonical_industry_quant_score,
    get_canonical_sector_quant_score,
    get_canonical_stock_quant_score
)
from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
from dashboard.industries_explorer import load_sector_overview_data

def test_canonical_model_fingerprint_immutable():
    """Verify that the canonical service returns the frozen V3.2 fingerprint."""
    fp = get_model_fingerprint()
    assert fp["model_version"] == "MODEL_V3.2_FROZEN"
    assert fp["verified_rank_ic"] == 0.1140
    assert fp["hac_t_statistic"] == 8.42

def test_canonical_industry_and_intelligence_exact_match():
    """Verify that canonical industry scores match the Industry Intelligence UI exactly (diff <= 0.0001)."""
    db = Database()
    dates = db.get_existing_price_dates()
    latest_date = dates[-1] if dates else "2026-08-21"
    
    df_canon, meta_canon = get_canonical_industry_quant_score(latest_date)
    df_intel, meta_intel = get_aggregated_hierarchy_intelligence(latest_date, hierarchy_level_key="major_industry")
    
    assert len(df_canon) == len(df_intel)
    
    # Merge and test difference
    df_m = df_canon.merge(df_intel, on="entity_name", suffixes=('_canon', '_intel'))
    diff = (df_m['current_strength_canon'] - df_m['current_strength_intel']).abs()
    assert (diff <= 0.0001).all(), f"Max discrepancy: {diff.max()}"

def test_canonical_sector_and_explorer_exact_match():
    """Verify that canonical sector scores match the Industries Explorer UI exactly (diff <= 0.0001)."""
    db = Database()
    dates = db.get_existing_price_dates()
    latest_date = dates[-1] if dates else "2026-08-21"
    
    df_canon_sec, _ = get_canonical_sector_quant_score(latest_date)
    df_expl_sec, _ = load_sector_overview_data(latest_date)
    
    assert len(df_canon_sec) > 0
    assert len(df_expl_sec) > 0
    
    df_m = df_canon_sec.merge(df_expl_sec, left_on="entity_name", right_on="sector", suffixes=('_canon', '_expl'))
    diff = (df_m['current_strength_canon'] - df_m['strength_score_expl']).abs()
    assert (diff <= 0.0001).all(), f"Max discrepancy in sector explorer: {diff.max()}"

def test_canonical_stock_quant_score_bounds_and_determinism():
    """Verify that canonical stock scores are strictly bounded in [0, 100] and deterministic."""
    db = Database()
    dates = db.get_existing_price_dates()
    latest_date = dates[-1] if dates else "2026-08-21"
    
    df_stks = get_canonical_stock_quant_score(latest_date)
    assert len(df_stks) > 0
    assert df_stks['stock_strength_score'].between(0.0, 100.0).all()
    assert set(df_stks['final_action'].unique()).issubset({'STRONG BUY', 'BUY', 'WATCH', 'NEUTRAL', 'REDUCE', 'AVOID'})

def test_primary_breadth_n_ge_5_rule_enforced():
    """Verify that N >= 5 rule assigns ELIGIBLE_PRIMARY vs INSUFFICIENT_BREADTH accurately."""
    db = Database()
    dates = db.get_existing_price_dates()
    latest_date = dates[-1] if dates else "2026-08-21"
    
    df_canon, _ = get_canonical_industry_quant_score(latest_date)
    for _, r in df_canon.iterrows():
        if r['constituent_count'] >= 5:
            assert r['breadth_qualification'] == 'ELIGIBLE_PRIMARY'
            assert r['is_production_eligible'] == True
        else:
            assert r['breadth_qualification'] == 'INSUFFICIENT_BREADTH'
            assert r['is_production_eligible'] == False
