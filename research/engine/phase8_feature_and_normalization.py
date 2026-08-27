"""
Phase 8: Complete Feature Library (Groups A-K) & Point-in-Time Normalization Engine.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

def normalize_cross_section_point_in_time(df: pd.DataFrame, feature_cols: List[str], method: str = 'winsorized_zscore') -> pd.DataFrame:
    """
    Normalizes feature columns cross-sectionally per date using strictly point-in-time moments.
    """
    df_out = df.copy()
    
    for dt, grp in df_out.groupby('date'):
        indices = grp.index
        for col in feature_cols:
            if col not in grp.columns:
                continue
            vals = grp[col].values.astype(float)
            valid_mask = ~np.isnan(vals)
            
            if np.sum(valid_mask) < 3:
                continue

            valid_vals = vals[valid_mask]

            if method == 'zscore':
                m = np.mean(valid_vals)
                s = np.std(valid_vals)
                s = s if s > 1e-6 else 1.0
                df_out.loc[indices[valid_mask], col + '_norm'] = (valid_vals - m) / s

            elif method == 'rank_percentile':
                ranks = pd.Series(valid_vals).rank(pct=True).values
                df_out.loc[indices[valid_mask], col + '_norm'] = ranks

            elif method == 'winsorized_zscore':
                p5 = np.percentile(valid_vals, 5)
                p95 = np.percentile(valid_vals, 95)
                clipped = np.clip(valid_vals, p5, p95)
                m = np.mean(clipped)
                s = np.std(clipped)
                s = s if s > 1e-6 else 1.0
                df_out.loc[indices[valid_mask], col + '_norm'] = (clipped - m) / s

            elif method == 'robust_mad':
                med = np.median(valid_vals)
                mad = np.median(np.abs(valid_vals - med))
                mad = mad if mad > 1e-6 else 1.0
                df_out.loc[indices[valid_mask], col + '_norm'] = (valid_vals - med) / (1.4826 * mad)

    return df_out

def compute_constituent_concentration_metrics(df_stk: pd.DataFrame) -> pd.DataFrame:
    """
    Computes industry-level HHI and top constituent concentration point-in-time.
    """
    records = []
    for (d, ind), grp in df_stk.groupby(['date', 'basic_industry']):
        n_stk = len(grp)
        if n_stk == 0:
            continue
        
        turnovers = grp['turnover'].fillna(0).values if 'turnover' in grp.columns else np.ones(n_stk)
        tot_to = np.sum(turnovers)
        weights = turnovers / tot_to if tot_to > 0 else np.full(n_stk, 1.0 / n_stk)
        weights_sorted = np.sort(weights)[::-1]
        
        top1 = weights_sorted[0] if len(weights_sorted) > 0 else 1.0
        top2 = np.sum(weights_sorted[:2]) if len(weights_sorted) >= 2 else top1
        top3 = np.sum(weights_sorted[:3]) if len(weights_sorted) >= 3 else top2
        hhi = np.sum(weights ** 2)
        eff_n = 1.0 / hhi if hhi > 0 else 1.0

        records.append({
            'date': d,
            'basic_industry': ind,
            'constituent_count': n_stk,
            'top1_concentration': round(float(top1 * 100.0), 1),
            'top2_concentration': round(float(top2 * 100.0), 1),
            'top3_concentration': round(float(top3 * 100.0), 1),
            'hhi_index': round(float(hhi), 4),
            'effective_constituents': round(float(eff_n), 1)
        })

    return pd.DataFrame(records)
