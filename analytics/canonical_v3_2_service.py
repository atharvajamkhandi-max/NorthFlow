"""
Canonical Quantitative Scoring Service.
Single Source of Truth for Quantitative Scoring across all Website Pages.
Enforces Frozen Model Specification: MODEL_V3.2_FROZEN.
"""

import os
import sys
import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, Any, Tuple, Optional

from database.db import Database
from config.model_v3_2_frozen import (
    MODEL_V3_2_FINGERPRINT,
    FROZEN_INDUSTRY_FACTOR_WEIGHTS,
    FROZEN_STOCK_LEADERSHIP_WEIGHTS,
    FROZEN_REGIME_MULTIPLIERS,
    FROZEN_PROBABILISTIC_PARAMS
)

def get_model_fingerprint() -> Dict[str, Any]:
    """Returns the immutable MODEL_V3.2_FROZEN specification and fingerprint."""
    return MODEL_V3_2_FINGERPRINT.copy()

@st.cache_data(ttl=180)
def get_canonical_hierarchy_quant_scores(selected_date: str, hierarchy_level_key: str = "major_industry") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Computes canonical quantitative scores aggregated at the requested hierarchy level.
    (major_industry, macro_sector, specialized_subsector).
    """
    from dashboard.components.global_state import HIERARCHY_LEVELS, get_hierarchy_level
    
    if hierarchy_level_key is None or hierarchy_level_key not in HIERARCHY_LEVELS:
        hierarchy_level_key = get_hierarchy_level()
        
    meta = HIERARCHY_LEVELS[hierarchy_level_key]
    col_name = meta["col"]
    
    db = Database()
    conn = db.get_connection()

    # For macro_sector hierarchy level, source from stock_classification_master_v3
    # to ensure canonical and explorer use identical classification data
    if col_name == "macro_sector":
        sql = f"""
        SELECT
            v.symbol,
            v.company_name,
            v.sector AS macro_sector,
            v.industry,
            v.industry AS basic_industry,
            v.sector AS entity_name,
            COALESCE(m.close, 100.0) as close_price,
            COALESCE(m.return_1d, 0.0) as return_1d,
            COALESCE(m.return_5d, 0.0) as return_5d,
            COALESCE(m.return_20d, 0.0) as return_20d,
            COALESCE(m.rs_5d, 0.0) as rs_5d,
            COALESCE(m.rs_20d, 0.0) as rs_20d,
            COALESCE(m.volume_ratio, 1.0) as volume_ratio,
            COALESCE(m.above_20ema, 0) as above_20ema,
            COALESCE(m.above_50ema, 0) as above_50ema,
            COALESCE(m.above_200ema, 0) as above_200ema,
            COALESCE(m.is_breakout_20d, 0) as is_breakout_20d
        FROM stock_classification_master_v3 v
        LEFT JOIN stock_metrics m ON v.symbol = m.symbol AND m.date = ?
        WHERE v.sector IS NOT NULL
          AND v.sector NOT IN ('EXCHANGE TRADED FUNDS', 'UNCLASSIFIED', 'NEEDS_CLASSIFICATION');
        """
    else:
        sql = f"""
        SELECT
            s.symbol,
            s.company_name,
            s.macro_sector,
            s.industry,
            s.basic_industry,
            s.{col_name} as entity_name,
            COALESCE(m.close, 100.0) as close_price,
            COALESCE(m.return_1d, 0.0) as return_1d,
            COALESCE(m.return_5d, 0.0) as return_5d,
            COALESCE(m.return_20d, 0.0) as return_20d,
            COALESCE(m.rs_5d, 0.0) as rs_5d,
            COALESCE(m.rs_20d, 0.0) as rs_20d,
            COALESCE(m.volume_ratio, 1.0) as volume_ratio,
            COALESCE(m.above_20ema, 0) as above_20ema,
            COALESCE(m.above_50ema, 0) as above_50ema,
            COALESCE(m.above_200ema, 0) as above_200ema,
            COALESCE(m.is_breakout_20d, 0) as is_breakout_20d
        FROM stocks s
        LEFT JOIN stock_metrics m ON s.symbol = m.symbol AND m.date = ?
        WHERE s.active = 1 AND s.{col_name} IS NOT NULL;
        """
    df_raw = pd.read_sql(sql, conn, params=[selected_date])

    
    if df_raw.empty or df_raw['return_1d'].isna().all():
        latest_date = pd.read_sql("SELECT MAX(date) as max_d FROM stock_metrics", conn)['max_d'].iloc[0]
        if latest_date and latest_date != selected_date:
            df_raw = pd.read_sql(sql, conn, params=[latest_date])
            selected_date = latest_date
            
    if df_raw.empty:
        return pd.DataFrame(), {}

    # For non-macro_sector paths, also exclude pseudo-sectors
    if col_name != "macro_sector":
        EXCLUDE_SECTORS = {'EXCHANGE TRADED FUNDS', 'UNCLASSIFIED', 'NEEDS_CLASSIFICATION'}
        df_raw = df_raw[~df_raw['macro_sector'].isin(EXCLUDE_SECTORS)].copy()
        if df_raw.empty:
            return pd.DataFrame(), {}

    df_agg = df_raw.groupby('entity_name').agg(
        constituent_count=('symbol', 'count'),
        avg_return_1d=('return_1d', 'mean'),
        median_return_1d=('return_1d', 'median'),
        avg_return_5d=('return_5d', 'mean'),
        median_return_5d=('return_5d', 'median'),
        avg_return_20d=('return_20d', 'mean'),
        median_return_20d=('return_20d', 'median'),
        industry_rs_5d=('rs_5d', 'mean'),
        industry_rs_20d=('rs_20d', 'mean'),
        avg_volume_ratio=('volume_ratio', 'mean'),
        breadth_20=('above_20ema', lambda x: (x == 1).mean() * 100.0),
        breadth_50=('above_50ema', lambda x: (x == 1).mean() * 100.0),
        breadth_200=('above_200ema', lambda x: (x == 1).mean() * 100.0),
        breakout_percentage=('is_breakout_20d', lambda x: (x == 1).mean() * 100.0)
    ).reset_index()
    
    # 1. CANONICAL V3.2 CURRENT STRENGTH
    rs_norm = np.clip((df_agg['industry_rs_20d'] + 15.0) / 30.0 * 100.0, 0.0, 100.0)
    vol_norm = np.clip(df_agg['avg_volume_ratio'] / 2.0 * 100.0, 0.0, 100.0)
    w = FROZEN_INDUSTRY_FACTOR_WEIGHTS
    
    df_agg['current_strength'] = np.clip(
        w["breadth_50"] * df_agg['breadth_50'] +
        w["relative_strength_20d"] * rs_norm +
        w["breadth_20"] * df_agg['breadth_20'] +
        w["volume_strength"] * vol_norm,
        0.0, 100.0
    ).round(1)
    
    df_agg['score_today'] = df_agg['current_strength']
    df_agg['strength_score'] = df_agg['current_strength'] # Backward compatibility
    df_agg['momentum_score'] = np.clip((df_agg['avg_return_20d'] + 10.0) / 20.0 * 100.0, 0.0, 100.0).round(1)
    df_agg['breadth_score'] = df_agg['breadth_50'].round(1)
    df_agg['relative_strength_score'] = rs_norm.round(1)
    df_agg['trend_score'] = df_agg['breadth_20'].round(1)
    df_agg['volume_score'] = vol_norm.round(1)
    
    df_agg['accumulation_score'] = np.clip(0.50 * df_agg['breadth_50'] + 0.30 * vol_norm + 0.20 * rs_norm, 0.0, 100.0).round(1)
    df_agg['distribution_risk_score'] = np.clip(0.60 * (100.0 - df_agg['breadth_50']) + 0.40 * (100.0 - rs_norm), 0.0, 100.0).round(1)
    
    df_agg['score_5d_ago'] = np.clip(df_agg['score_today'] - df_agg['avg_return_5d'] * 0.8, 0.0, 100.0).round(1)
    df_agg['score_1d_ago'] = np.clip(df_agg['score_today'] - df_agg['avg_return_1d'] * 0.5, 0.0, 100.0).round(1)
    df_agg['leadership_acceleration'] = (df_agg['score_today'] - df_agg['score_5d_ago']).round(1)
    df_agg['score_change_5d'] = df_agg['leadership_acceleration']
    df_agg['score_change_1d'] = (df_agg['score_today'] - df_agg['score_1d_ago']).round(1)
    
    # 2. MARKET REGIME
    mkt_breadth_50 = float(df_agg['breadth_50'].mean())
    mkt_rs = float(df_agg['industry_rs_20d'].median())
    if mkt_breadth_50 >= 60.0 and mkt_rs > 1.5:
        market_regime = "STRONG_BULL"
        regime_mult = FROZEN_REGIME_MULTIPLIERS["STRONG_BULL"]
    elif mkt_breadth_50 >= 50.0:
        market_regime = "WEAK_BULL"
        regime_mult = FROZEN_REGIME_MULTIPLIERS["WEAK_BULL"]
    elif mkt_breadth_50 >= 40.0:
        market_regime = "SIDEWAYS"
        regime_mult = FROZEN_REGIME_MULTIPLIERS["SIDEWAYS"]
    elif mkt_breadth_50 >= 25.0:
        market_regime = "WEAK_BEAR"
        regime_mult = FROZEN_REGIME_MULTIPLIERS["WEAK_BEAR"]
    else:
        market_regime = "STRONG_BEAR"
        regime_mult = FROZEN_REGIME_MULTIPLIERS["STRONG_BEAR"]
        
    # 3. CANONICAL V3.2 EXPECTED RETURNS & PROBABILITIES
    base_sig = (df_agg['current_strength'] - 50.0) / 10.0
    df_agg['exp_return_1d'] = ((0.12 * base_sig) * regime_mult).round(2)
    df_agg['exp_return_5d'] = ((0.70 * base_sig) * regime_mult).round(2)
    df_agg['exp_return_20d'] = ((2.80 * base_sig) * regime_mult).round(2)
    df_agg['exp_return_60d'] = ((6.00 * base_sig) * regime_mult).round(2)
    df_agg['expected_excess_return_20d'] = df_agg['exp_return_20d']
    
    # Prediction Intervals (df=5, sigma=7.0%)
    df_agg['P10_20d'] = (df_agg['exp_return_20d'] - 10.5).round(1)
    df_agg['P25_20d'] = (df_agg['exp_return_20d'] - 5.2).round(1)
    df_agg['P50_20d'] = df_agg['exp_return_20d']
    df_agg['P75_20d'] = (df_agg['exp_return_20d'] + 5.2).round(1)
    df_agg['P90_20d'] = (df_agg['exp_return_20d'] + 10.5).round(1)
    df_agg['P95_20d'] = (df_agg['exp_return_20d'] + 14.8).round(1)
    df_agg['prediction_uncertainty'] = (df_agg['P90_20d'] - df_agg['P10_20d']).round(1)
    
    # Probabilities
    z_score = df_agg['exp_return_20d'] / 7.0
    df_agg['prob_positive'] = np.clip(100.0 / (1.0 + np.exp(-z_score * 1.2)), 5.0, 95.0).round(1)
    df_agg['prob_outperform'] = df_agg['prob_positive']
    df_agg['prob_gt_5pct'] = np.clip(100.0 / (1.0 + np.exp(-(z_score - 0.7) * 1.2)), 2.0, 90.0).round(1)
    df_agg['prob_gt_8pct'] = np.clip(100.0 / (1.0 + np.exp(-(z_score - 1.1) * 1.2)), 1.0, 80.0).round(1)
    df_agg['prob_gt_10pct'] = np.clip(100.0 / (1.0 + np.exp(-(z_score - 1.4) * 1.2)), 0.5, 70.0).round(1)
    df_agg['prob_gt_15pct'] = np.clip(100.0 / (1.0 + np.exp(-(z_score - 2.1) * 1.2)), 0.1, 50.0).round(1)
    
    # Confidence & Risk
    dispersion = np.abs(df_agg['avg_return_20d'] - df_agg['median_return_20d'])
    df_agg['confidence_score'] = np.clip(
        df_agg['breadth_50'] * 0.4 +
        (100.0 - np.clip(dispersion * 5.0, 0, 50)) * 0.3 +
        np.clip(df_agg['constituent_count'] * 2.0, 10, 100) * 0.3,
        15.0, 95.0
    ).round(1)
    
    df_agg['risk_score'] = np.clip(
        (100.0 - df_agg['breadth_50']) * 0.4 +
        np.clip(dispersion * 6.0, 0, 50) * 0.4 +
        (20.0 if market_regime in ['WEAK_BEAR', 'STRONG_BEAR'] else 5.0),
        10.0, 95.0
    ).round(1)
    
    df_agg['model_agreement'] = np.clip(85.0 - (dispersion * 4.0), 40.0, 98.0).round(1)
    df_agg['best_horizon'] = np.where(df_agg['leadership_acceleration'] >= 4.0, '5D_MOMENTUM', '20D_CORE_SWING')
    
    # Forward Opportunity Score
    df_agg['forward_opportunity_score'] = np.clip(
        0.50 * df_agg['current_strength'] +
        0.25 * df_agg['prob_outperform'] +
        0.25 * (df_agg['exp_return_20d'].clip(-10, 15) + 10.0) / 25.0 * 100.0,
        0.0, 100.0
    ).round(1)
    
    # Flow State & Action
    conditions_flow = [
        (df_agg['current_strength'] >= 65.0) & (df_agg['score_change_5d'] >= 0),
        (df_agg['current_strength'] >= 50.0),
        (df_agg['current_strength'] < 35.0) & (df_agg['score_change_5d'] < 0),
        (df_agg['current_strength'] < 50.0)
    ]
    choices_flow = ['ACCUMULATION', 'EXPANSION', 'MARKDOWN', 'DISTRIBUTION']
    df_agg['flow_state'] = np.select(conditions_flow, choices_flow, default='NEUTRAL')
    
    conditions_trend = [
        (df_agg['breadth_50'] >= 75.0) & (df_agg['breadth_20'] >= 75.0),
        (df_agg['breadth_50'] >= 50.0),
        (df_agg['breadth_50'] < 30.0) & (df_agg['breadth_20'] < 30.0),
        (df_agg['breadth_50'] < 50.0)
    ]
    choices_trend = ['STRONG BULLISH', 'BULLISH', 'STRONG BEARISH', 'BEARISH']
    df_agg['trend_rating'] = np.select(conditions_trend, choices_trend, default='SIDEWAYS')
    
    conditions_action = [
        (df_agg['current_strength'] >= 70.0) & (df_agg['exp_return_20d'] > 3.0),
        (df_agg['current_strength'] >= 55.0) & (df_agg['exp_return_20d'] > 1.0),
        (df_agg['current_strength'] >= 45.0) & (df_agg['score_change_5d'] > 3.0),
        (df_agg['current_strength'] >= 40.0) & (df_agg['current_strength'] < 55.0),
        (df_agg['current_strength'] < 30.0) & (df_agg['exp_return_20d'] < -3.0),
        (df_agg['current_strength'] < 40.0)
    ]
    choices_action = ['STRONG BUY', 'BUY', 'WATCH', 'NEUTRAL', 'AVOID', 'REDUCE']
    df_agg['final_action'] = np.select(conditions_action, choices_action, default='NEUTRAL')
    
    # Primary Industry Breadth Rule (N >= 5)
    df_agg['is_production_eligible'] = df_agg['constituent_count'] >= 5
    df_agg['breadth_qualification'] = np.where(df_agg['is_production_eligible'], 'ELIGIBLE_PRIMARY', 'INSUFFICIENT_BREADTH')
    
    if col_name != 'macro_sector':
        df_sec_map = df_raw.groupby('entity_name')['macro_sector'].agg(lambda x: x.mode().iloc[0] if not x.empty else 'Other').reset_index()
        df_agg = df_agg.merge(df_sec_map, on='entity_name', how='left')
    else:
        df_agg['macro_sector'] = df_agg['entity_name']
        
    df_agg[col_name] = df_agg['entity_name']
    
    market_meta = {
        "model_version": MODEL_V3_2_FINGERPRINT["model_version"],
        "feature_version": MODEL_V3_2_FINGERPRINT["feature_version"],
        "verified_rank_ic": MODEL_V3_2_FINGERPRINT["verified_rank_ic"],
        "market_regime": market_regime,
        "regime_multiplier": regime_mult,
        "market_breadth_50": mkt_breadth_50,
        "market_rs": mkt_rs,
        "total_entities": len(df_agg),
        "production_eligible_count": int(df_agg['is_production_eligible'].sum()),
        "insufficient_breadth_count": int((~df_agg['is_production_eligible']).sum()),
        "selected_date": selected_date,
        "hierarchy_level": hierarchy_level_key,
        "hierarchy_col": col_name,
        "hierarchy_label": meta["label"],
        "hierarchy_plural": meta["plural"],
        "hierarchy_badge": meta["badge"]
    }
    
    return df_agg, market_meta

def get_canonical_industry_quant_score(selected_date: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Returns canonical Major Industry scores (168 industries)."""
    return get_canonical_hierarchy_quant_scores(selected_date, hierarchy_level_key="major_industry")

def get_canonical_sector_quant_score(selected_date: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Returns canonical Macro Sector scores (48 sectors)."""
    return get_canonical_hierarchy_quant_scores(selected_date, hierarchy_level_key="macro_sector")

@st.cache_data(ttl=180)
def get_canonical_stock_quant_score(selected_date: str, symbol: Optional[str] = None) -> pd.DataFrame:
    """
    Returns canonical point-in-time quantitative scores for all constituent stocks.
    Uses frozen V3.2 factor parameters.
    """
    db = Database()
    conn = db.get_connection()
    
    sym_filter = f"AND s.symbol = '{symbol}'" if symbol else ""
    sql_stocks = f"""
    SELECT s.symbol, s.company_name, s.macro_sector, s.industry, s.basic_industry,
           COALESCE(m.close, 100.0) as close_price,
           COALESCE(m.return_1d, 0.0) as return_1d,
           COALESCE(m.return_5d, 0.0) as return_5d,
           COALESCE(m.return_20d, 0.0) as return_20d,
           COALESCE(m.rs_5d, 0.0) as rs_5d,
           COALESCE(m.rs_20d, 0.0) as rs_20d,
           COALESCE(m.volume_ratio, 1.0) as volume_ratio,
           COALESCE(m.above_50ema, 0) as above_50ema,
           COALESCE(m.above_20ema, 0) as above_20ema,
           COALESCE(m.is_breakout_20d, 0) as is_breakout_20d
    FROM stocks s
    LEFT JOIN stock_metrics m ON s.symbol = m.symbol AND m.date = ?
    WHERE s.active = 1 {sym_filter}
    """
    df_stocks = pd.read_sql(sql_stocks, conn, params=[selected_date])
    
    if df_stocks.empty:
        latest_d = pd.read_sql("SELECT MAX(date) as max_d FROM stock_metrics", conn)['max_d'].iloc[0]
        df_stocks = pd.read_sql(sql_stocks, conn, params=[latest_d])
        
    if df_stocks.empty:
        return pd.DataFrame()
        
    # Calculate canonical stock composite score
    rs_n = np.clip((df_stocks['rs_20d'] + 15.0) / 30.0 * 100.0, 0.0, 100.0)
    vol_n = np.clip(df_stocks['volume_ratio'] / 2.0 * 100.0, 0.0, 100.0)
    
    w = FROZEN_INDUSTRY_FACTOR_WEIGHTS
    df_stocks['stock_strength_score'] = np.clip(
        w["breadth_50"] * (df_stocks['above_50ema'] * 100.0) +
        w["relative_strength_20d"] * rs_n +
        w["breadth_20"] * (df_stocks['above_20ema'] * 100.0) +
        w["volume_strength"] * vol_n,
        0.0, 100.0
    ).round(1)
    
    df_stocks['score_today'] = df_stocks['stock_strength_score']
    
    # Action Recommendation
    conditions = [
        (df_stocks['stock_strength_score'] >= 70.0) & (df_stocks['rs_20d'] > 3.0),
        (df_stocks['stock_strength_score'] >= 55.0) & (df_stocks['rs_20d'] > 0.0),
        (df_stocks['stock_strength_score'] >= 45.0) & (df_stocks['return_5d'] > 2.0),
        (df_stocks['stock_strength_score'] >= 40.0),
        (df_stocks['stock_strength_score'] < 30.0) & (df_stocks['rs_20d'] < -3.0),
        (df_stocks['stock_strength_score'] < 40.0)
    ]
    choices = ['STRONG BUY', 'BUY', 'WATCH', 'NEUTRAL', 'AVOID', 'REDUCE']
    df_stocks['final_action'] = np.select(conditions, choices, default='NEUTRAL')
    
    df_stocks['model_version'] = MODEL_V3_2_FINGERPRINT["model_version"]
    df_stocks['data_date'] = selected_date
    
    return df_stocks
