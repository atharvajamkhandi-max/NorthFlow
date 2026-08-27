"""
Two-Sided CUSUM and Page-Hinkley Change Point Detection.
"""
import pandas as pd
import numpy as np

def detect_change_points_cusum(series: pd.Series, threshold: float = 2.5, drift: float = 0.5) -> pd.Series:
    """
    Two-Sided Cumulative Sum (CUSUM) filter for detecting regime shifts.
    """
    s_pos = 0.0
    s_neg = 0.0
    signals = []
    
    # Normalize series to standard deviations
    mean_val = series.mean()
    std_val = series.std() + 1e-6
    z_series = (series - mean_val) / std_val
    
    for val in z_series:
        s_pos = max(0.0, s_pos + val - drift)
        s_neg = min(0.0, s_neg + val + drift)
        
        if s_pos > threshold:
            signals.append(1) # Bullish change-point
            s_pos = 0.0
        elif s_neg < -threshold:
            signals.append(-1) # Bearish change-point
            s_neg = 0.0
        else:
            signals.append(0)
            
    return pd.Series(signals, index=series.index)
