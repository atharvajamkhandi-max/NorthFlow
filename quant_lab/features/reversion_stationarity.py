"""
Mean Reversion, Ornstein-Uhlenbeck Half-Life, and Stationarity Metrics.
"""
import pandas as pd
import numpy as np

def compute_mean_reversion_factors(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Computes:
    - Price Z-Score: (Price - MA_n) / STD_n
    - Ornstein-Uhlenbeck Half-Life proxy
    """
    df_out = df.copy()
    
    ma20 = df_out.groupby('symbol')['close'].transform(lambda x: x.rolling(window, min_periods=5).mean())
    std20 = df_out.groupby('symbol')['close'].transform(lambda x: x.rolling(window, min_periods=5).std())
    df_out['price_zscore_20d'] = ((df_out['close'] - ma20) / (std20 + 1e-6)).clip(-4.0, 4.0).fillna(0.0)
    
    # OU half-life proxy via rolling autocorrelation
    ret_1d = df_out.groupby('symbol')['close'].pct_change()
    ret_lag = df_out.groupby('symbol')['close'].pct_change().shift(1)
    
    cov_ret = df_out.groupby('symbol')['close'].transform(
        lambda s: (ret_1d.loc[s.index] * ret_lag.loc[s.index]).rolling(window, min_periods=5).mean()
    )
    var_ret = df_out.groupby('symbol')['close'].transform(
        lambda s: (ret_lag.loc[s.index]**2).rolling(window, min_periods=5).mean()
    )
    rho = (cov_ret / (var_ret + 1e-6)).clip(-0.99, 0.99)
    
    # half_life = -ln(2) / ln(abs(rho) + 1e-6)
    df_out['ou_half_life_20d'] = (-np.log(2.0) / np.log(abs(rho) + 1e-4)).clip(1.0, 60.0).fillna(20.0)
    
    return df_out
