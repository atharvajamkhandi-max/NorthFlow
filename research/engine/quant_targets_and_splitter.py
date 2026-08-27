"""
Phase D & E: Point-in-Time Forward Target Generator & Walk-Forward Splitter with Purge/Embargo.
Calculates forward returns (5D, 10D, 20D, 30D, 60D), excess returns vs Market and Sector,
and creates strictly non-overlapping walk-forward training/validation/holdout splits.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

class QuantTargetsAndSplitter:
    @staticmethod
    def compute_forward_targets(df_ind: pd.DataFrame, df_bench: pd.DataFrame) -> pd.DataFrame:
        print("Computing multi-horizon forward targets (5D, 10D, 20D, 30D, 60D) & excess returns...")
        df = df_ind.sort_values(['basic_industry', 'date']).reset_index(drop=True).copy()

        # Benchmark forward returns
        b_df = df_bench.sort_values('date').reset_index(drop=True).copy()
        for h in [5, 10, 20, 30, 60]:
            b_df[f'bench_fwd_{h}d'] = (b_df['close'].shift(-h) / b_df['close'] - 1.0) * 100.0

        b_dict = b_df.set_index('date').to_dict('index')

        # Industry forward returns per basic_industry
        records = []
        for ind, grp in df.groupby('basic_industry'):
            sub = grp.sort_values('date').reset_index(drop=True).copy()
            rets_1d = sub['industry_return_1d_median'].fillna(0.0).values
            n_rows = len(rets_1d)
            
            for h in [5, 10, 20, 30, 60]:
                fwd_h = np.full(n_rows, np.nan)
                for i in range(n_rows):
                    if i + h < n_rows:
                        fwd_h[i] = np.sum(rets_1d[i+1 : i+h+1])
                
                sub[f'future_return_{h}D'] = np.round(fwd_h, 2)
                sub[f'bench_fwd_{h}D'] = sub['date'].map(lambda d: b_dict.get(d, {}).get(f'bench_fwd_{h}d', 0.0)).fillna(0.0).round(2)
                sub[f'future_excess_return_{h}D'] = (sub[f'future_return_{h}D'] - sub[f'bench_fwd_{h}D']).round(2)
                
                # Binary classification targets
                sub[f'outperform_market_{h}D'] = (sub[f'future_excess_return_{h}D'] > 0.0).astype(float)
                sub[f'positive_return_{h}D'] = (sub[f'future_return_{h}D'] > 0.0).astype(float)

            records.append(sub)

        df_out = pd.concat(records, ignore_index=True)
        return df_out

    @staticmethod
    def create_walk_forward_splits(all_dates: List[str], train_window: int = 140, val_window: int = 40, purge_embargo: int = 20) -> List[Dict[str, Any]]:
        """
        Creates expanding-window walk-forward splits with mandatory Purge and Embargo periods.
        """
        splits = []
        holdout_dates = all_dates[-50:]
        train_val_dates = all_dates[:-50]

        step = val_window
        start_idx = 0

        while start_idx + train_window + purge_embargo + val_window <= len(train_val_dates):
            train_start = 0
            train_end = start_idx + train_window
            val_start = train_end + purge_embargo
            val_end = val_start + val_window
            
            if val_end > len(train_val_dates):
                break

            train_slice = train_val_dates[train_start:train_end]
            val_slice = train_val_dates[val_start:val_end]

            splits.append({
                "split_id": len(splits) + 1,
                "train_start_date": train_slice[0],
                "train_end_date": train_slice[-1],
                "val_start_date": val_slice[0],
                "val_end_date": val_slice[-1],
                "train_sessions": len(train_slice),
                "val_sessions": len(val_slice),
                "purge_embargo_sessions": purge_embargo
            })

            start_idx += step

        print(f"Generated {len(splits)} walk-forward evaluation folds with {purge_embargo}-day purge & embargo.")
        return splits
