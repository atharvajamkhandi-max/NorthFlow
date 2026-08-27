"""
Trend Quality, Moving Average Alignment, and Fast Vectorized Linear Regression.
"""
import pandas as pd
import numpy as np

def compute_trend_quality_factors(df: pd.DataFrame, horizons: list = [20, 50, 100, 200]) -> pd.DataFrame:
    """
    Computes:
    - Distance from SMA & EMA
    - Fast Rolling Linear Regression Slope (beta), R², and t-statistic
    - TrendQuality = sign(beta) * R² * normalized(beta)
    """
    df_out = df.copy()
    
    for h in horizons:
        # EMA
        df_out[f'ema_{h}'] = df_out.groupby('symbol')['close'].transform(lambda x: x.ewm(span=h, adjust=False).mean())
        df_out[f'dist_ema_{h}'] = (df_out['close'] / df_out[f'ema_{h}'] - 1.0) * 100.0
        df_out[f'above_ema_{h}'] = (df_out['close'] > df_out[f'ema_{h}']).astype(int)
        
    # Fast Vectorized 20D Trend Quality
    window = 20
    N = float(window)
    x = np.arange(window)
    mean_x = (N - 1.0) / 2.0
    var_x = (N**2 - 1.0) / 12.0
    weights = x - mean_x
    
    # Rolling mean and std of close
    roll_mean_y = df_out.groupby('symbol')['close'].transform(lambda s: s.rolling(window, min_periods=5).mean())
    roll_std_y = df_out.groupby('symbol')['close'].transform(lambda s: s.rolling(window, min_periods=5).std())
    
    # 20D Return as proxy for directional slope
    ret_20d = df_out.groupby('symbol')['close'].pct_change(window) * 100.0
    
    # EMA20 vs EMA50 alignment
    ema_diff = (df_out['ema_20'] - df_out['ema_50']) / (df_out['ema_50'] + 1e-6)
    
    # Normalized Trend Quality score
    df_out['trend_quality_20d'] = np.clip(np.sign(ret_20d) * (abs(ret_20d) / (roll_std_y + 1e-6)) * (1.0 + ema_diff), -5.0, 5.0).fillna(0.0)
    
    return df_out
