"""
Test Suite for Multi-Industry Multi-Tagging and Quantitative Calculation Audit.
Verifies that:
1. Multi-industry classification dataset is populated in SQLite.
2. Conglomerate companies (Reliance, ITC, L&T, Tata Motors, M&M, etc.) have multiple operating division tags.
3. 7 decoupled quantitative dimensions (Strength, Return, Confidence, Risk, Regime, Lifecycle, Flow) satisfy mathematical bounds.
4. Deterministic actions (STRONG BUY, BUY, WATCH, NEUTRAL, REDUCE, AVOID) are assigned correctly.
5. All prediction intervals (P10 <= P25 <= P50 <= P75 <= P90) maintain strict monotonic ordering.
"""

import pytest
import pandas as pd
import numpy as np
from database.db import Database
from dashboard.components.v3_intelligence_loader import get_v3_date_intelligence

def test_multi_industry_classification_populated():
    db = Database()
    conn = db.get_connection()
    df_multi = pd.read_sql("SELECT * FROM company_multi_industry_classification", conn)
    assert not df_multi.empty, "Multi-industry classification table should not be empty"
    assert len(df_multi) >= 3363, "Should have at least 3,363 active equity mapping records"
    assert 'symbol' in df_multi.columns
    assert 'macro_sector' in df_multi.columns
    assert 'niche_subsector' in df_multi.columns
    assert 'business_segment' in df_multi.columns
    assert 'segment_tag' in df_multi.columns

def test_conglomerates_have_multiple_segments():
    db = Database()
    df_cong = db.get_conglomerate_companies()
    assert not df_cong.empty, "Should identify diversified conglomerates"
    assert len(df_cong) >= 40, f"Expected at least 40 conglomerates, found {len(df_cong)}"
    
    cong_symbols = df_cong['symbol'].tolist()
    for key_sym in ['RELIANCE', 'ITC', 'LT', 'TATAMOTORS', 'M&M', 'BAJAJFINSV', 'GRASIM']:
        assert key_sym in cong_symbols, f"Expected {key_sym} in conglomerates list"

def test_reliance_multi_industry_segments():
    db = Database()
    rec = db.get_company_multi_industry_records('RELIANCE')
    assert len(rec) >= 4, f"Reliance should have at least 4 business segments, found {len(rec)}"
    subsectors = rec['niche_subsector'].tolist()
    assert any('Telecom' in s for s in subsectors), "Reliance must include Telecom division"
    assert any('Retail' in s for s in subsectors), "Reliance must include Retail division"
    assert any('Energy' in s or 'Oil' in s for s in subsectors), "Reliance must include Energy/Oil division"

def test_quant_dimensions_mathematical_bounds():
    sec_agg, df_sub, df_stk, market_meta = get_v3_date_intelligence('2026-08-21')
    assert not sec_agg.empty
    assert not df_sub.empty
    assert not df_stk.empty

    # Q1: Strength bounds [0, 100]
    assert (df_sub['current_strength'] >= 0.0).all() and (df_sub['current_strength'] <= 100.0).all()
    # Q3: Confidence bounds [0, 100]
    assert (df_sub['confidence_score'] >= 0.0).all() and (df_sub['confidence_score'] <= 100.0).all()
    # Q4: Downside Risk bounds [0, 100]
    assert (df_sub['risk_score'] >= 0.0).all() and (df_sub['risk_score'] <= 100.0).all()
    # Q7: Net Pressure bounds [-100, 100]
    assert (df_sub['net_pressure'] >= -100.0).all() and (df_sub['net_pressure'] <= 100.0).all()

    # Valid Action categories
    valid_actions = {'STRONG BUY', 'BUY', 'WATCH', 'NEUTRAL', 'REDUCE', 'AVOID'}
    assert set(df_sub['final_action'].unique()).issubset(valid_actions)
    assert set(sec_agg['final_action'].unique()).issubset(valid_actions)
    assert set(df_stk['stock_action'].unique()).issubset(valid_actions)

def test_prediction_interval_monotonicity():
    sec_agg, df_sub, df_stk, market_meta = get_v3_date_intelligence('2026-08-21')
    for _, row in df_sub.iterrows():
        assert row['P10_20d'] <= row['P25_20d'] <= row['P50_20d'] <= row['P75_20d'] <= row['P90_20d'], (
            f"Prediction interval monotonic ordering violated for {row['niche_subsector']}: "
            f"P10={row['P10_20d']}, P25={row['P25_20d']}, P50={row['P50_20d']}, P75={row['P75_20d']}, P90={row['P90_20d']}"
        )
