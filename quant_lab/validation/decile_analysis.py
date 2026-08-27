"""
Monotonic Decile and Quantile Analysis.
"""
import pandas as pd
import numpy as np

def compute_decile_spreads(df: pd.DataFrame, score_col: str, target_col: str) -> pd.DataFrame:
    """Computes Decile 1 to 10 performance and top-bottom spread."""
    bins = []
    for d, grp in df.groupby('date'):
        if len(grp) >= 10:
            grp = grp.copy()
            grp['Decile'] = pd.qcut(grp[score_col].rank(method='first'), q=10, labels=False) + 1
            bins.append(grp[['Decile', target_col]])
            
    if not bins:
        return pd.DataFrame()
        
    all_b = pd.concat(bins, ignore_index=True)
    summary = all_b.groupby('Decile').agg(
        Avg_Return=(target_col, 'mean'),
        Win_Rate=(target_col, lambda x: (x > 0).mean() * 100.0)
    ).reset_index().sort_values('Decile', ascending=False)
    
    return summary
