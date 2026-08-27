"""
Value-at-Risk (VaR) and Expected Shortfall (CVaR).
"""
import numpy as np

def compute_portfolio_var(returns: np.ndarray, confidence: float = 0.95) -> dict:
    """Computes Historical Value-at-Risk (VaR) and Conditional VaR (CVaR)."""
    if len(returns) == 0:
        return {"VaR": 0.0, "CVaR": 0.0}
    sorted_ret = np.sort(returns)
    cutoff = int((1.0 - confidence) * len(sorted_ret))
    var = -sorted_ret[cutoff]
    cvar = -sorted_ret[:cutoff].mean() if cutoff > 0 else var
    return {"VaR": round(float(var), 2), "CVaR": round(float(cvar), 2)}
