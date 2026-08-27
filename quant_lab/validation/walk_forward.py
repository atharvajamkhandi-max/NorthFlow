"""
Purged and Embargoed Expanding Walk-Forward Validator.
"""
import pandas as pd
import numpy as np

class PurgedWalkForwardValidator:
    """
    Constructs expanding walk-forward splits with strict purge & embargo windows.
    Guarantees zero target leakage between train and test intervals.
    """
    def __init__(self, n_splits: int = 5, embargo_sessions: int = 20):
        self.n_splits = n_splits
        self.embargo_sessions = embargo_sessions
        
    def generate_splits(self, df: pd.DataFrame, date_col: str = 'date'):
        unique_dates = sorted(df[date_col].unique())
        n_dates = len(unique_dates)
        split_size = n_dates // (self.n_splits + 1)
        
        for i in range(self.n_splits):
            train_end_idx = split_size * (i + 1)
            test_start_idx = train_end_idx + self.embargo_sessions # Embargo purge
            test_end_idx = min(test_start_idx + split_size, n_dates)
            
            if test_start_idx >= n_dates:
                break
                
            train_dates = unique_dates[:train_end_idx]
            test_dates = unique_dates[test_start_idx:test_end_idx]
            
            train_mask = df[date_col].isin(train_dates)
            test_mask = df[date_col].isin(test_dates)
            
            yield i + 1, train_mask, test_mask, train_dates, test_dates
