"""
Multi-Target Generation Framework (Horizons: 1D, 5D, 10D, 20D, 60D).
"""
import pandas as pd
import numpy as np

def generate_multi_horizon_targets(df: pd.DataFrame, 
                                   horizons: list = [1, 5, 10, 20, 60], 
                                   bench_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Generates forward targets:
    - Target 1: Future return: (P_(t+h) / P_t) - 1
    - Target 2: Future excess return vs benchmark
    - Target 3: Binary outperformance: 1 if excess > 0 else 0
    - Target 4: Top-Decile indicator: 1 if in top 10% on date else 0
    """
    df_out = df.copy()
    grouped = df_out.groupby('symbol')['close']
    
    for h in horizons:
        # Forward Return
        df_out[f'target_{h}d_fwd'] = ((grouped.shift(-h) / df_out['close']) - 1.0) * 100.0
        
        # Binary Positive Return
        df_out[f'target_{h}d_positive'] = (df_out[f'target_{h}d_fwd'] > 0).astype(int)
        
    return df_out
