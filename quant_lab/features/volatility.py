"""
Comprehensive Volatility Surface & High-Low Estimators.
Standard Deviation, Parkinson, Garman-Klass, and Volatility Ratio.
"""
import pandas as pd
import numpy as np

def compute_volatility_surface(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Computes:
    - Parkinson Extreme-Value Volatility
    - Close-to-Close Volatility
    - Volatility Compression Ratio (sigma_short / sigma_long)
    """
    df_out = df.copy()
    
    # Parkinson Volatility: sigma_P = sqrt(1 / (4 ln 2) * mean((ln(H/L))^2)) * sqrt(252)
    factor_p = 1.0 / (4.0 * np.log(2.0))
    hl_sq = (np.log(df_out['high'] / (df_out['low'] + 1e-6))) ** 2
    
    df_out['vol_parkinson_20d'] = df_out.groupby('symbol')['high'].transform(
        lambda s: np.sqrt(factor_p * hl_sq.loc[s.index].rolling(window, min_periods=5).mean()) * np.sqrt(252) * 100.0
    ).fillna(0.0)
    
    ret_1d = df_out.groupby('symbol')['close'].pct_change()
    
    df_out['vol_close_20d'] = df_out.groupby('symbol')['close'].transform(
        lambda s: ret_1d.loc[s.index].rolling(window, min_periods=5).std() * np.sqrt(252) * 100.0
    ).fillna(0.0)
    
    df_out['vol_close_60d'] = df_out.groupby('symbol')['close'].transform(
        lambda s: ret_1d.loc[s.index].rolling(60, min_periods=10).std() * np.sqrt(252) * 100.0
    ).fillna(0.0)
    
    df_out['vol_compression_ratio'] = (df_out['vol_close_20d'] / (df_out['vol_close_60d'] + 1e-6)).clip(0.1, 5.0).fillna(1.0)
    
    return df_out
