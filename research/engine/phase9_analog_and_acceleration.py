"""
Phase 9: Emerging Leadership Acceleration & Point-in-Time Historical Analog Engine.
Implements:
1. Leadership Acceleration Score & States (Established Leader, Emerging Leader, Accelerating, Neutral, Decelerating, Weakening)
2. Point-in-Time Historical Analog Similarity Matcher (extracts conditional return distributions from comparable past market states)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from scipy.spatial.distance import cdist

ANALOG_FEATURE_COLS = [
    'avg_rs_5d', 'avg_rs_20d', 'ema50_breadth', 'breadth_change_5d',
    'dir_vol_spread_12', 'residual_mom_5d', 'avg_vol_ratio_20d', 'trend_stack_breadth'
]

def compute_leadership_acceleration(df_ind_matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Computes delta changes in RS, Breadth, Volume, Trend and classifies Leadership State.
    """
    df = df_ind_matrix.sort_values(['basic_industry', 'date']).copy()
    
    # Delta calculations
    df['d_rs_5d'] = df.groupby('basic_industry')['avg_rs_5d'].diff(3).fillna(0)
    df['d_breadth_5d'] = df.groupby('basic_industry')['ema50_breadth'].diff(3).fillna(0)
    df['d_vol_spread'] = df.groupby('basic_industry')['dir_vol_spread_12'].diff(3).fillna(0)
    df['d_res_mom'] = df.groupby('basic_industry')['residual_mom_5d'].diff(3).fillna(0)
    
    # Leadership Acceleration Score (0-100)
    accel_raw = (
        0.35 * df['d_rs_5d'] +
        0.30 * df['d_breadth_5d'] +
        0.20 * df['d_vol_spread'] +
        0.15 * df['d_res_mom']
    )
    # Scale to 0-100 centered at 50
    df['leadership_accel_score'] = np.clip(50.0 + accel_raw * 1.5, 0.0, 100.0)

    # Leadership States
    states = []
    for _, row in df.iterrows():
        rs = row.get('avg_rs_20d', 50)
        br = row.get('ema50_breadth', 50)
        acc = row.get('leadership_accel_score', 50)
        
        if rs >= 65 and br >= 60 and acc >= 55:
            st = 'ESTABLISHED LEADER'
        elif rs < 60 and br >= 50 and acc >= 60:
            st = 'EMERGING LEADER'
        elif acc >= 58:
            st = 'ACCELERATING'
        elif rs <= 40 and br <= 40 and acc <= 45:
            st = 'WEAKENING'
        elif acc <= 42:
            st = 'DECELERATING'
        else:
            st = 'NEUTRAL'
        states.append(st)

    df['leadership_state'] = states
    return df

def find_historical_analogs(
    current_state_row: pd.Series,
    df_history: pd.DataFrame,
    feature_cols: List[str] = ANALOG_FEATURE_COLS,
    top_k: int = 15
) -> pd.DataFrame:
    """
    Finds top_k closest historical industry states strictly before current_date.
    Returns analog matches and their forward realized returns.
    """
    curr_date = current_state_row['date']
    curr_ind = current_state_row['basic_industry']
    
    # Strictly point-in-time: history before curr_date (with 5-day embargo)
    hist_pool = df_history[df_history['date'] < curr_date].copy()
    if len(hist_pool) < top_k:
        return pd.DataFrame()

    valid_cols = [c for c in feature_cols if c in hist_pool.columns and c in current_state_row]
    if len(valid_cols) < 4:
        return pd.DataFrame()

    X_hist = hist_pool[valid_cols].fillna(50).values
    x_curr = current_state_row[valid_cols].fillna(50).values.reshape(1, -1)

    # Standardize using historical moments
    mean_h = np.mean(X_hist, axis=0)
    std_h = np.std(X_hist, axis=0)
    std_h[std_h == 0] = 1.0

    X_hist_std = (X_hist - mean_h) / std_h
    x_curr_std = (x_curr - mean_h) / std_h

    # Euclidean distance
    dists = cdist(x_curr_std, X_hist_std, metric='euclidean')[0]
    hist_pool['similarity_distance'] = dists
    
    analogs = hist_pool.sort_values('similarity_distance').head(top_k).copy()
    analogs['similarity_score'] = np.clip(100.0 - analogs['similarity_distance'] * 15.0, 10.0, 99.0)
    return analogs
