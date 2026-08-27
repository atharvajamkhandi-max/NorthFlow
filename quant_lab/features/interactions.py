"""
Nonlinear Price-Volume and Momentum-Delivery Cross Interactions.
"""
import pandas as pd
import numpy as np

def compute_nonlinear_interactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes nonlinear cross-term interactions:
    - Return * Volume Ratio
    - Relative Strength * Delivery Intensity
    - Trend Quality * Delivery Z-score
    """
    df_out = df.copy()
    
    ret = df_out.get('ret_20d', pd.Series(0.0, index=df_out.index))
    vol = df_out.get('vol_ratio_20d', pd.Series(1.0, index=df_out.index))
    deliv = df_out.get('deliv_directional_intensity', pd.Series(0.0, index=df_out.index))
    trend = df_out.get('trend_quality_20d', pd.Series(0.0, index=df_out.index))
    
    df_out['interact_ret_vol'] = ret * vol
    df_out['interact_ret_deliv'] = ret * deliv
    df_out['interact_trend_deliv'] = trend * deliv
    
    return df_out
