"""
Corporate action adjustments for continuous returns.
"""
import pandas as pd
import numpy as np

def adjust_for_splits(df: pd.DataFrame, threshold: float = 0.40) -> pd.DataFrame:
    """
    Identifies discrete price drops (|1d return| > threshold) and adjusts historical prices backward.
    """
    df_out = df.copy()
    if 'symbol' not in df_out.columns or 'close' not in df_out.columns:
        return df_out
        
    for sym, grp in df_out.groupby('symbol'):
        sub = grp.sort_values('date').reset_index()
        pct = sub['close'].pct_change()
        split_locs = sub[pct < -threshold].index.tolist()
        
        for loc in split_locs:
            if loc > 0:
                ratio = sub.loc[loc - 1, 'close'] / sub.loc[loc, 'close']
                split_date = sub.loc[loc, 'date']
                mask = (df_out['symbol'] == sym) & (df_out['date'] < split_date)
                for c in ['open', 'high', 'low', 'close']:
                    if c in df_out.columns:
                        df_out.loc[mask, c] = df_out.loc[mask, c] / ratio
    return df_out
