"""
Dynamic Position Sizing: Inverse Volatility, Equal Weight, and Risk Parity.
"""
import pandas as pd
import numpy as np

def compute_inverse_vol_weights(volatilities: pd.Series) -> pd.Series:
    """Computes normalized weights inversely proportional to volatility."""
    inv_vol = 1.0 / (volatilities + 1e-6)
    return inv_vol / inv_vol.sum()
