"""
Multi-Horizon Lead-Lag Cross-Correlation and Granger Causality Discovery Engine.
"""
import pandas as pd
import numpy as np
from scipy import stats

def compute_lead_lag_correlations(feature_series: pd.Series, 
                                  target_series: pd.Series, 
                                  horizons: list = [1, 2, 3, 5, 10, 15, 20, 30, 40, 60]) -> pd.DataFrame:
    """
    Computes Pearson, Spearman Rank IC, and Lead-Time Profile across multiple forward horizons.
    Corr(Feature_t, Target_(t+h))
    """
    results = []
    
    for h in horizons:
        fwd_target = target_series.shift(-h)
        valid = pd.DataFrame({'f': feature_series, 't': fwd_target}).dropna()
        
        if len(valid) >= 20:
            pearson_r, p_val = stats.pearsonr(valid['f'], valid['t'])
            spearman_ic, ic_p = stats.spearmanr(valid['f'], valid['t'])
            
            results.append({
                "Horizon_Days": h,
                "Pearson_r": round(pearson_r, 4),
                "Rank_IC": round(spearman_ic, 4),
                "p_value": float(f"{ic_p:.2e}"),
                "Observations": len(valid)
            })
            
    return pd.DataFrame(results)

def eval_granger_causality(feature_series: pd.Series, target_series: pd.Series, max_lag: int = 5) -> dict:
    """
    Tests if Feature Granger-causes Target using an autoregressive bivariate regression.
    """
    df_reg = pd.DataFrame({'y': target_series, 'x': feature_series}).dropna()
    if len(df_reg) < 30:
        return {"F_stat": 0.0, "p_val": 1.0, "Granger_Causes": False}
        
    # Restricted model: y_t = c + sum(a_i * y_(t-i))
    # Unrestricted: y_t = c + sum(a_i * y_(t-i)) + sum(b_i * x_(t-i))
    y = df_reg['y'].values
    x = df_reg['x'].values
    n = len(y) - max_lag
    
    Y = y[max_lag:]
    X_restr = np.column_stack([np.ones(n)] + [y[max_lag - i - 1: -i - 1 if i > 0 else None][:n] for i in range(max_lag)])
    X_unrestr = np.column_stack([X_restr] + [x[max_lag - i - 1: -i - 1 if i > 0 else None][:n] for i in range(max_lag)])
    
    # Residual sum of squares
    beta_r, res_r, _, _ = np.linalg.lstsq(X_restr, Y, rcond=None)
    beta_u, res_u, _, _ = np.linalg.lstsq(X_unrestr, Y, rcond=None)
    
    rss_r = np.sum((Y - X_restr @ beta_r)**2)
    rss_u = np.sum((Y - X_unrestr @ beta_u)**2)
    
    df1 = max_lag
    df2 = n - 2 * max_lag - 1
    if df2 <= 0 or rss_u == 0:
        return {"F_stat": 0.0, "p_val": 1.0, "Granger_Causes": False}
        
    f_stat = ((rss_r - rss_u) / df1) / (rss_u / df2)
    p_val = 1.0 - stats.f.cdf(f_stat, df1, df2)
    
    return {
        "F_stat": round(f_stat, 2),
        "p_val": round(p_val, 4),
        "Granger_Causes": bool(p_val < 0.05)
    }
