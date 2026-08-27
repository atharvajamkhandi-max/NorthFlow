"""
Industry Market Breadth, Breadth Impulse, and Return Dispersion.
"""
import pandas as pd
import numpy as np

def compute_industry_breadth_and_dispersion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes:
    - Industry Breadth (% stocks > 20 EMA, 50 EMA, 200 EMA)
    - Breadth Impulse = (Breadth_t - Breadth_(t-k)) / std(Breadth)
    - Cross-Sectional Return Dispersion = std(stock returns within industry)
    """
    df_out = df.copy()
    
    if 'industry' not in df_out.columns or 'date' not in df_out.columns:
        return df_out
        
    # Stock-level indicators
    if 'above_ema_50' not in df_out.columns:
        ema50 = df_out.groupby('symbol')['close'].transform(lambda x: x.ewm(span=50, adjust=False).mean())
        df_out['above_ema_50'] = (df_out['close'] > ema50).astype(int)
        
    if 'above_ema_20' not in df_out.columns:
        ema20 = df_out.groupby('symbol')['close'].transform(lambda x: x.ewm(span=20, adjust=False).mean())
        df_out['above_ema_20'] = (df_out['close'] > ema20).astype(int)
        
    # Group by (industry, date)
    breadth_grp = df_out.groupby(['industry', 'date']).agg(
        industry_breadth_50=('above_ema_50', lambda x: x.mean() * 100.0),
        industry_breadth_20=('above_ema_20', lambda x: x.mean() * 100.0),
        industry_return_1d=('close', lambda x: x.pct_change().mean() * 100.0 if len(x)>1 else 0.0),
        industry_dispersion=('close', lambda x: x.pct_change().std() * 100.0 if len(x)>2 else 0.0)
    ).reset_index()
    
    # Breadth Impulse per industry
    breadth_grp['breadth_impulse_10d'] = breadth_grp.groupby('industry')['industry_breadth_50'].transform(
        lambda x: (x - x.shift(10)) / (x.rolling(20, min_periods=5).std() + 1e-6)
    ).fillna(0.0).clip(-3.0, 3.0)
    
    df_out = df_out.merge(breadth_grp, on=['industry', 'date'], how='left')
    return df_out
