"""
Multi-Horizon Simple and Log Returns across 1D to 252D.
"""
import pandas as pd
import numpy as np

def compute_multi_horizon_returns(df: pd.DataFrame, 
                                  horizons: list = [1, 2, 3, 5, 10, 15, 20, 30, 40, 60, 90, 120, 180, 252]) -> pd.DataFrame:
    """
    Computes simple and log returns across multiple horizons.
    R_t(k) = P_t / P_(t-k) - 1
    r_t(k) = ln(P_t / P_(t-k))
    """
    df_res = df.copy()
    grouped = df_res.groupby('symbol')['close']
    
    for h in horizons:
        df_res[f'ret_{h}d'] = grouped.pct_change(h) * 100.0
        df_res[f'log_ret_{h}d'] = np.log(df_res['close'] / grouped.shift(h))
        
    return df_res
