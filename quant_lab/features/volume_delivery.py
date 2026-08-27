"""
Cash Volume and Exchange-Reported Delivery Multi-Horizon Factors.
"""
import pandas as pd
import numpy as np

def compute_volume_delivery_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes:
    - Volume / MA20, Volume Z-Score
    - Delivery Percentage, Delivery Volume Acceleration
    - Directional Delivery Intensity = Delivery Ratio * sign(Close - Open)
    - Delivery Breadth & Abnormal Delivery Accumulation
    """
    df_out = df.copy()
    
    # Volume Ratios
    vol_ma20 = df_out.groupby('symbol')['volume'].transform(lambda x: x.rolling(20, min_periods=5).mean())
    vol_std20 = df_out.groupby('symbol')['volume'].transform(lambda x: x.rolling(20, min_periods=5).std())
    df_out['vol_ratio_20d'] = (df_out['volume'] / (vol_ma20 + 1e-6)).clip(0.1, 10.0)
    df_out['vol_zscore_20d'] = ((df_out['volume'] - vol_ma20) / (vol_std20 + 1e-6)).clip(-3.0, 5.0)
    
    # Delivery Dynamics
    if 'deliv_qty' in df_out.columns and 'deliv_per' in df_out.columns:
        deliv_ma20 = df_out.groupby('symbol')['deliv_qty'].transform(lambda x: x.rolling(20, min_periods=5).mean())
        deliv_std20 = df_out.groupby('symbol')['deliv_qty'].transform(lambda x: x.rolling(20, min_periods=5).std())
        
        df_out['deliv_ratio_20d'] = (df_out['deliv_qty'] / (deliv_ma20 + 1e-6)).clip(0.1, 10.0)
        df_out['deliv_zscore_20d'] = ((df_out['deliv_qty'] - deliv_ma20) / (deliv_std20 + 1e-6)).clip(-3.0, 5.0)
        
        # Directional Accumulation (Positive on up days with high delivery, negative on down days)
        price_dir = np.sign(df_out['close'] - df_out['open'])
        df_out['deliv_directional_intensity'] = df_out['deliv_ratio_20d'] * price_dir
        
    return df_out
