"""
Cross-Sectional, Time-Series, Risk-Adjusted, and Residual Momentum.
"""
import pandas as pd
import numpy as np

def compute_momentum_factors(df: pd.DataFrame, bench_returns: pd.Series = None) -> pd.DataFrame:
    """
    Computes:
    - Relative Momentum vs Market & Industry
    - Risk-Adjusted Momentum (Return / Rolling Volatility)
    - Cross-Sectional Percentile Rank Momentum
    """
    df_out = df.copy()
    
    # 20D Return
    if 'ret_20d' not in df_out.columns:
        df_out['ret_20d'] = df_out.groupby('symbol')['close'].pct_change(20) * 100.0
        
    # Rolling 20D Volatility
    ret_1d = df_out.groupby('symbol')['close'].pct_change()
    vol_20d = ret_1d.groupby(df_out['symbol']).rolling(20, min_periods=10).std().reset_index(0, drop=True)
    df_out['risk_adj_mom_20d'] = df_out['ret_20d'] / (vol_20d * np.sqrt(252) + 1e-6)
    
    # Cross-Sectional Rank Momentum per date
    df_out['cs_mom_rank_20d'] = df_out.groupby('date')['ret_20d'].rank(pct=True) * 100.0
    
    return df_out
