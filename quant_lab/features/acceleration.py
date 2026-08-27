"""
First Derivative (Acceleration) and Second Derivative (Curvature).
"""
import pandas as pd
import numpy as np

def compute_acceleration_and_curvature(df: pd.DataFrame, 
                                       signal_col: str = 'ret_20d', 
                                       lookbacks: list = [3, 5, 10, 20]) -> pd.DataFrame:
    """
    Acceleration_t = Signal_t - Signal_(t-k)
    Curvature_t = Acceleration_t - Acceleration_(t-k)
    """
    df_out = df.copy()
    grouped = df_out.groupby('symbol')[signal_col]
    
    for k in lookbacks:
        acc_col = f'{signal_col}_acc_{k}d'
        curv_col = f'{signal_col}_curv_{k}d'
        
        df_out[acc_col] = grouped.diff(k)
        df_out[curv_col] = df_out.groupby('symbol')[acc_col].diff(k)
        
    return df_out
