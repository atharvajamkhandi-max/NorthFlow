"""
Multi-Horizon Forecasting Targets & Excursion Calculation Engine.
Calculates:
- Forward Absolute Returns (R1, R3, R5, R10, R15, R20)
- Forward Benchmark Returns (B1, B3, B5, B10, B15, B20)
- Forward Excess Returns (ER1, ER3, ER5, ER10, ER15, ER20)
- Maximum Adverse Excursion (MAE) and Maximum Favorable Excursion (MFE) over 5D, 10D, 20D
- Binary Directional Outperformance Targets (Y5, Y10, Y20)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

def compute_forecasting_targets(df_prices: pd.DataFrame, df_bench: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Benchmark forward returns
    df_b = df_bench.sort_values('date').copy()
    b_dates = df_b['date'].tolist()
    b_closes = df_b['close'].tolist()
    b_map = dict(zip(b_dates, b_closes))
    
    b_fwd_rets = {}
    for h in [1, 3, 5, 10, 15, 20]:
        b_fwd_rets[f'bench_fwd_{h}d'] = {}
        for i, d in enumerate(b_dates):
            if i + h < len(b_dates):
                ret = (b_closes[i + h] / b_closes[i] - 1.0) * 100.0
                b_fwd_rets[f'bench_fwd_{h}d'][d] = ret
            else:
                b_fwd_rets[f'bench_fwd_{h}d'][d] = np.nan

    # Compute industry daily prices
    df_p = df_prices[df_prices['basic_industry'] != 'UNKNOWN'].copy()
    df_ind_p = df_p.groupby(['date', 'basic_industry'])['close'].mean().reset_index()
    df_ind_p = df_ind_p.sort_values(['basic_industry', 'date']).reset_index(drop=True)

    # Multi-horizon forward returns and excursions
    for h in [1, 3, 5, 10, 15, 20]:
        df_ind_p[f'fwd_ret_{h}d'] = df_ind_p.groupby('basic_industry')['close'].shift(-h) / df_ind_p['close'] - 1.0
        df_ind_p[f'fwd_ret_{h}d'] *= 100.0
        df_ind_p[f'bench_fwd_{h}d'] = df_ind_p['date'].map(b_fwd_rets[f'bench_fwd_{h}d'])
        df_ind_p[f'excess_fwd_{h}d'] = df_ind_p[f'fwd_ret_{h}d'] - df_ind_p[f'bench_fwd_{h}d']

    # Max Adverse & Favorable Excursions over next 5D, 10D, 20D
    for h in [5, 10, 20]:
        df_ind_p[f'mfe_{h}d'] = np.nan
        df_ind_p[f'mae_{h}d'] = np.nan

    # Excursion loop per industry
    records = []
    for ind, grp in df_ind_p.groupby('basic_industry'):
        sub = grp.sort_values('date').copy()
        closes = sub['close'].values
        n = len(closes)
        
        mfes_5, maes_5 = [], []
        mfes_10, maes_10 = [], []
        mfes_20, maes_20 = [], []
        
        for i in range(n):
            # 5D
            if i + 5 < n:
                fwd_window = closes[i+1 : i+6]
                mfes_5.append((np.max(fwd_window) / closes[i] - 1.0) * 100.0)
                maes_5.append((np.min(fwd_window) / closes[i] - 1.0) * 100.0)
            else:
                mfes_5.append(np.nan)
                maes_5.append(np.nan)
            
            # 10D
            if i + 10 < n:
                fwd_window = closes[i+1 : i+11]
                mfes_10.append((np.max(fwd_window) / closes[i] - 1.0) * 100.0)
                maes_10.append((np.min(fwd_window) / closes[i] - 1.0) * 100.0)
            else:
                mfes_10.append(np.nan)
                maes_10.append(np.nan)

            # 20D
            if i + 20 < n:
                fwd_window = closes[i+1 : i+21]
                mfes_20.append((np.max(fwd_window) / closes[i] - 1.0) * 100.0)
                maes_20.append((np.min(fwd_window) / closes[i] - 1.0) * 100.0)
            else:
                mfes_20.append(np.nan)
                maes_20.append(np.nan)

        sub['mfe_5d'] = mfes_5
        sub['mae_5d'] = maes_5
        sub['mfe_10d'] = mfes_10
        sub['mae_10d'] = maes_10
        sub['mfe_20d'] = mfes_20
        sub['mae_20d'] = maes_20
        records.append(sub)

    df_targets = pd.concat(records, ignore_index=True)
    
    # Binary targets
    df_targets['Y5_pos'] = (df_targets['fwd_ret_5d'] > 0).astype(float)
    df_targets['Y5_excess'] = (df_targets['excess_fwd_5d'] > 0).astype(float)
    df_targets['Y10_pos'] = (df_targets['fwd_ret_10d'] > 0).astype(float)
    df_targets['Y10_excess'] = (df_targets['excess_fwd_10d'] > 0).astype(float)
    df_targets['Y20_pos'] = (df_targets['fwd_ret_20d'] > 0).astype(float)
    df_targets['Y20_excess'] = (df_targets['excess_fwd_20d'] > 0).astype(float)

    print(f"Target calculation complete: {len(df_targets)} industry session records with forward returns and excursions.")
    return df_targets, pd.DataFrame(b_fwd_rets)
