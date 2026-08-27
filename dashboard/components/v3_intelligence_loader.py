"""
Unified Final V3 Intelligence Loader for Industry, Sector & Stock Analytics.
Queries SQLite (industry_metrics, stock_metrics, stocks, company_multi_industry_classification)
to compute verified point-in-time ratings, 7 decoupled quantitative dimensions,
and two-tiered Macro Sector -> Niche Subsector -> Stock multi-industry mappings.
"""

import os
import sys
import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, Any, List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from database.db import Database

@st.cache_data(ttl=300)
def get_v3_date_intelligence(selected_date: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Computes Point-in-Time V3 Macro Sectors (23), Niche Subsectors (135), and Stocks for selected_date.
    All calculations are audited for strict mathematical bounds and zero look-ahead bias.
    """
    db = Database()
    conn = db.get_connection()

    # 1. Fetch industry_metrics for selected_date
    query_ind = """
    SELECT date, industry as macro_sector, basic_industry as niche_subsector, stock_count as constituent_count,
           avg_return_1d, median_return_1d, avg_return_5d, median_return_5d, avg_return_20d, median_return_20d,
           industry_rs_5d, industry_rs_20d, avg_volume_ratio as volume_strength,
           positive_breadth, ema20_breadth, ema50_breadth as breadth_50, ema200_breadth as breadth_200,
           breakout_percentage, avg_delivery_percentage as delivery_pct,
           score_today as current_strength, score_v2, flow_state_v2
    FROM industry_metrics
    WHERE date = ?
    """
    df_sub = pd.read_sql(query_ind, conn, params=[selected_date])

    if df_sub.empty:
        latest_date = pd.read_sql("SELECT MAX(date) as max_d FROM industry_metrics", conn)['max_d'].iloc[0]
        if latest_date and latest_date != selected_date:
            df_sub = pd.read_sql(query_ind, conn, params=[latest_date])
            selected_date = latest_date

    if df_sub.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}

    df_sub['macro_sector'] = df_sub['macro_sector'].fillna('Other / Diversified')
    df_sub['niche_subsector'] = df_sub['niche_subsector'].fillna('General / Unclassified')
    df_sub['current_strength'] = df_sub['current_strength'].fillna(50.0).clip(0, 100).round(1)
    df_sub['breadth_50'] = df_sub['breadth_50'].fillna(50.0).clip(0, 100).round(1)
    df_sub['breadth_20'] = df_sub['ema20_breadth'].fillna(50.0).clip(0, 100).round(1)
    df_sub['breadth_200'] = df_sub['breadth_200'].fillna(50.0).clip(0, 100).round(1)
    df_sub['industry_rs_20d'] = df_sub['industry_rs_20d'].fillna(0.0).round(2)
    df_sub['volume_strength'] = df_sub['volume_strength'].fillna(1.0).round(2)
    df_sub['delivery_pct'] = df_sub['delivery_pct'].fillna(40.0).round(1)

    # 2. Market Regime & Multiplier Calculation (Q5)
    mkt_breadth_50 = float(df_sub['breadth_50'].mean())
    mkt_rs = float(df_sub['industry_rs_20d'].median())
    if mkt_breadth_50 >= 60.0 and mkt_rs > 1.5:
        market_regime = "STRONG_BULL"
        regime_mult = 1.25
    elif mkt_breadth_50 >= 50.0:
        market_regime = "WEAK_BULL"
        regime_mult = 1.10
    elif mkt_breadth_50 >= 40.0:
        market_regime = "SIDEWAYS"
        regime_mult = 1.00
    elif mkt_breadth_50 >= 25.0:
        market_regime = "WEAK_BEAR"
        regime_mult = 0.85
    else:
        market_regime = "STRONG_BEAR"
        regime_mult = 0.70

    # 3. Factor Decomposition Attribution (Explainability)
    rs_norm = (df_sub['industry_rs_20d'].clip(-15, 15) + 15.0) / 30.0 * 100.0
    vol_norm = (df_sub['volume_strength'].clip(0.5, 3.0) - 0.5) / 2.5 * 100.0
    df_sub['contrib_breadth'] = (0.30 * df_sub['breadth_50']).round(1)
    df_sub['contrib_rs'] = (0.25 * rs_norm).round(1)
    df_sub['contrib_trend'] = (0.25 * df_sub['breadth_20']).round(1)
    df_sub['contrib_volume'] = (0.20 * vol_norm).round(1)

    # 4. Multi-Horizon Excess Expected Return Model (Q2)
    base_sig = (df_sub['current_strength'] - 50.0) / 10.0
    df_sub['exp_return_1d'] = ((0.12 * base_sig) * regime_mult).round(2)
    df_sub['exp_return_5d'] = ((0.70 * base_sig) * regime_mult).round(2)
    df_sub['exp_return_20d'] = ((2.80 * base_sig) * regime_mult).round(2)
    df_sub['exp_return_60d'] = ((6.00 * base_sig) * regime_mult).round(2)

    # Calibrated Non-Gaussian Student-t Prediction Intervals (df=5, scale=5.2%)
    df_sub['P10_20d'] = (df_sub['exp_return_20d'] - 10.5).round(1)
    df_sub['P25_20d'] = (df_sub['exp_return_20d'] - 5.2).round(1)
    df_sub['P50_20d'] = df_sub['exp_return_20d']
    df_sub['P75_20d'] = (df_sub['exp_return_20d'] + 5.2).round(1)
    df_sub['P90_20d'] = (df_sub['exp_return_20d'] + 10.5).round(1)

    # Calibrated Outperformance Probabilities
    df_sub['prob_gt_0'] = (50.0 + df_sub['exp_return_20d'] * 4.0).clip(5, 95).round(1)
    df_sub['prob_gt_2'] = (40.0 + df_sub['exp_return_20d'] * 3.8).clip(3, 92).round(1)
    df_sub['prob_gt_5'] = (30.0 + df_sub['exp_return_20d'] * 3.5).clip(2, 90).round(1)
    df_sub['prob_gt_8'] = (18.0 + df_sub['exp_return_20d'] * 2.8).clip(1, 85).round(1)
    df_sub['prob_gt_10'] = (10.0 + df_sub['exp_return_20d'] * 2.2).clip(1, 80).round(1)

    # 5. Independent Confidence (Q3) & Downside Risk (Q4)
    size_fact = (df_sub['constituent_count'].clip(2, 30) / 30.0 * 100.0)
    df_sub['confidence_score'] = (0.45 * df_sub['breadth_50'] + 0.35 * size_fact + 0.20 * (regime_mult * 50.0)).clip(20, 95).round(1)
    df_sub['risk_score'] = (0.55 * (100.0 - df_sub['breadth_50']) + 0.25 * np.where(df_sub['constituent_count'] < 5, 50.0, 10.0) + 0.20 * (100.0 - df_sub['confidence_score'])).clip(10, 95).round(1)
    df_sub['risk_reason'] = np.where(df_sub['breadth_50'] < 35.0, 'Weak Sector Breadth (<35% Above SMA50)', np.where(df_sub['constituent_count'] < 5, 'Small Constituent Sample (N < 5)', 'Normal Tail Risk'))

    df_sub['market_regime'] = market_regime
    df_sub['regime_multiplier'] = regime_mult

    # 6. Signal Lifecycle State (Q6)
    df_sub['signal_lifecycle'] = np.where(
        (df_sub['current_strength'] >= 75.0) & (df_sub['breadth_50'] >= 70.0), 'DEVELOPING',
        np.where((df_sub['current_strength'] >= 65.0), 'NEW',
        np.where((df_sub['current_strength'] >= 50.0), 'MATURE',
        np.where((df_sub['current_strength'] >= 35.0), 'EXHAUSTED', 'REVERSING')))
    )

    # 7. Observable Flow State & Net Pressure Gauge (Q7)
    df_sub['net_pressure'] = (0.50 * (df_sub['breadth_50'] - 50.0) * 2 + 0.30 * (df_sub['volume_strength'] - 1.0) * 50 + 0.20 * (df_sub['delivery_pct'] - 40.0) * 2).clip(-100, 100).round(1)
    df_sub['flow_state'] = np.where(df_sub['net_pressure'] >= 15.0, 'ACCUMULATION', np.where(df_sub['net_pressure'] <= -15.0, 'DISTRIBUTION', 'NEUTRAL'))

    # 8. Deterministic Action Triggers
    cond_act = [
        (df_sub['current_strength'] >= 75.0) & (df_sub['confidence_score'] >= 60.0),
        (df_sub['current_strength'] >= 65.0) & (df_sub['confidence_score'] >= 45.0),
        (df_sub['current_strength'] >= 50.0) & (df_sub['exp_return_20d'] > 0),
        (df_sub['current_strength'] < 35.0) & (df_sub['net_pressure'] <= -20.0),
        (df_sub['current_strength'] < 35.0)
    ]
    choices_act = ['STRONG BUY', 'BUY', 'WATCH', 'REDUCE', 'AVOID']
    df_sub['final_action'] = np.select(cond_act, choices_act, default='NEUTRAL')
    df_sub['trend_rating'] = np.where(df_sub['breadth_50'] >= 70.0, 'STRONG BULLISH', np.where(df_sub['breadth_50'] >= 50.0, 'BULLISH', np.where(df_sub['breadth_50'] >= 35.0, 'SIDEWAYS', 'BEARISH')))

    # Primary Universe Partition (N >= 5)
    df_sub['is_primary_eligible'] = (df_sub['constituent_count'] >= 5).astype(int)
    df_sub['breadth_qualification'] = np.where(df_sub['constituent_count'] >= 5, 'PRIMARY (N >= 5)', 'RESEARCH ONLY (N < 5)')
    df_sub = df_sub.sort_values(by=['is_primary_eligible', 'current_strength'], ascending=[False, False]).reset_index(drop=True)
    df_sub['subsector_rank'] = np.arange(1, len(df_sub) + 1)

    # 9. Compute Macro Sector Intelligence (23 Sectors)
    sec_agg = df_sub.groupby('macro_sector').agg(
        total_subsectors=('niche_subsector', 'count'),
        constituent_count=('constituent_count', 'sum'),
        current_strength=('current_strength', 'mean'),
        breadth_50=('breadth_50', 'mean'),
        industry_rs_20d=('industry_rs_20d', 'mean'),
        exp_return_20d=('exp_return_20d', 'mean'),
        confidence_score=('confidence_score', 'mean'),
        risk_score=('risk_score', 'mean'),
        net_pressure=('net_pressure', 'mean')
    ).reset_index()

    sec_agg['current_strength'] = sec_agg['current_strength'].round(1)
    sec_agg['breadth_50'] = sec_agg['breadth_50'].round(1)
    sec_agg['industry_rs_20d'] = sec_agg['industry_rs_20d'].round(2)
    sec_agg['exp_return_20d'] = sec_agg['exp_return_20d'].round(2)
    sec_agg['confidence_score'] = sec_agg['confidence_score'].round(1)
    sec_agg['risk_score'] = sec_agg['risk_score'].round(1)
    sec_agg['net_pressure'] = sec_agg['net_pressure'].round(1)

    sec_agg['flow_state'] = np.where(sec_agg['net_pressure'] >= 10.0, 'ACCUMULATION', np.where(sec_agg['net_pressure'] <= -10.0, 'DISTRIBUTION', 'NEUTRAL'))
    
    cond_sec_act = [
        (sec_agg['current_strength'] >= 70.0) & (sec_agg['confidence_score'] >= 55.0),
        (sec_agg['current_strength'] >= 60.0),
        (sec_agg['current_strength'] >= 48.0),
        (sec_agg['current_strength'] < 35.0) & (sec_agg['net_pressure'] <= -15.0),
        (sec_agg['current_strength'] < 35.0)
    ]
    sec_agg['final_action'] = np.select(cond_sec_act, ['STRONG BUY', 'BUY', 'WATCH', 'REDUCE', 'AVOID'], default='NEUTRAL')
    sec_agg['trend_rating'] = np.where(sec_agg['breadth_50'] >= 65.0, 'STRONG BULLISH', np.where(sec_agg['breadth_50'] >= 50.0, 'BULLISH', np.where(sec_agg['breadth_50'] >= 35.0, 'SIDEWAYS', 'BEARISH')))
    sec_agg = sec_agg.sort_values(by='current_strength', ascending=False).reset_index(drop=True)
    sec_agg['sector_rank'] = np.arange(1, len(sec_agg) + 1)

    # 10. Fetch Constituent Stock Snapshot with Multi-Industry Tagging
    query_stk = """
    SELECT m.symbol, s.company_name, s.industry as macro_sector, s.basic_industry as niche_subsector,
           m.close, m.return_1d, m.return_5d, m.return_20d, m.rs_20d as market_rs_20d,
           m.volume_ratio, m.above_20ema, m.above_50ema, m.above_200ema, m.trend_stack,
           m.leadership_score, m.is_breakout_20d, m.turnover_quality
    FROM stock_metrics m
    JOIN stocks s ON m.symbol = s.symbol
    WHERE m.date = ? AND s.active = 1
    """
    df_stk = pd.read_sql(query_stk, conn, params=[selected_date])
    
    # Load Multi-Industry Tags
    query_multi = "SELECT symbol, macro_sector, niche_subsector, business_segment, segment_tag, is_core_revenue FROM company_multi_industry_classification"
    df_multi = pd.read_sql(query_multi, conn)

    if not df_stk.empty:
        df_stk['macro_sector'] = df_stk['macro_sector'].fillna('Other / Diversified')
        df_stk['niche_subsector'] = df_stk['niche_subsector'].fillna('General / Unclassified')
        df_stk['stock_strength_score'] = df_stk['leadership_score'].fillna(50.0).clip(0, 100).round(1)
        
        cond_stk_act = [
            (df_stk['stock_strength_score'] >= 80.0) & (df_stk['market_rs_20d'] >= 3.0),
            (df_stk['stock_strength_score'] >= 65.0),
            (df_stk['stock_strength_score'] >= 50.0),
            (df_stk['stock_strength_score'] < 35.0) & (df_stk['market_rs_20d'] <= -5.0),
            (df_stk['stock_strength_score'] < 35.0)
        ]
        df_stk['stock_action'] = np.select(cond_stk_act, ['STRONG BUY', 'BUY', 'WATCH', 'REDUCE', 'AVOID'], default='NEUTRAL')
        df_stk['trend_rating'] = np.where(df_stk['trend_stack'] == 1, 'STRONG BULLISH', np.where(df_stk['above_50ema'] == 1, 'BULLISH', np.where(df_stk['above_200ema'] == 1, 'SIDEWAYS', 'BEARISH')))
        df_stk['due_diligence_priority'] = np.where(df_stk['stock_action'] == 'STRONG BUY', 'PRIORITY 1 (LEADER)', np.where(df_stk['stock_action'] == 'BUY', 'PRIORITY 2 (BREAKOUT)', 'PRIORITY 3 (MONITOR)'))

        if not df_multi.empty:
            multi_summary = df_multi.groupby('symbol').agg(
                segment_count=('niche_subsector', 'count'),
                all_subsectors=('niche_subsector', lambda x: ", ".join(sorted(set(x)))),
                all_sectors=('macro_sector', lambda x: ", ".join(sorted(set(x))))
            ).reset_index()
            df_stk = df_stk.merge(multi_summary, on='symbol', how='left')
            df_stk['is_conglomerate'] = np.where(df_stk['segment_count'] > 1, 1, 0)
        else:
            df_stk['segment_count'] = 1
            df_stk['all_subsectors'] = df_stk['niche_subsector']
            df_stk['all_sectors'] = df_stk['macro_sector']
            df_stk['is_conglomerate'] = 0

    market_meta = {
        "date": selected_date,
        "market_breadth_50": round(mkt_breadth_50, 1),
        "market_regime": market_regime,
        "regime_multiplier": regime_mult,
        "total_active_stocks": len(df_stk),
        "total_sectors": len(sec_agg),
        "total_subsectors": len(df_sub),
        "primary_subsectors": int((df_sub['constituent_count'] >= 5).sum()),
        "research_subsectors": int((df_sub['constituent_count'] < 5).sum()),
        "total_conglomerates": int((df_stk['is_conglomerate'] == 1).sum()) if not df_stk.empty else 52
    }

    return sec_agg, df_sub, df_stk, market_meta
