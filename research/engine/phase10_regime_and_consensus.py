"""
Phase 10: Market Regime Conditioning, Model Consensus & Historical Analog Quality Engine.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from scipy.spatial.distance import cdist

ANALOG_FEATURE_COLS = [
    'avg_rs_5d', 'avg_rs_20d', 'ema50_breadth', 'breadth_change_5d',
    'dir_vol_spread_12', 'residual_mom_5d', 'avg_vol_ratio_20d', 'trend_stack_breadth'
]

def determine_market_regime(df_bench: pd.DataFrame, as_of_date: str) -> Dict[str, Any]:
    """
    Identifies the macroeconomic/benchmark regime strictly point-in-time.
    """
    bench_sub = df_bench[df_bench['date'] <= as_of_date].sort_values('date').copy()
    if len(bench_sub) < 5:
        return {'regime': 'NEUTRAL / CONSOLIDATION', 'volatility_tier': 'NORMAL', 'risk_state': 'NEUTRAL'}

    closes = bench_sub['close'].values
    ret_5d = (closes[-1] / closes[-5] - 1.0) * 100.0 if len(closes) >= 5 else 0.0
    ret_20d = (closes[-1] / closes[-20] - 1.0) * 100.0 if len(closes) >= 20 else 0.0

    # Volatility of daily returns
    daily_rets = np.diff(closes) / closes[:-1]
    vol_20d = np.std(daily_rets[-20:]) * np.sqrt(252) * 100.0 if len(daily_rets) >= 20 else 15.0

    if ret_5d > 1.5 and ret_20d > 2.0:
        regime = 'BULL_EXPANSION'
        risk_state = 'RISK_ON'
    elif ret_5d < -1.5 and ret_20d < -2.0:
        regime = 'BEAR_CONTRACTION'
        risk_state = 'RISK_OFF'
    elif abs(ret_5d) <= 1.5:
        regime = 'SIDEWAYS_ROTATION'
        risk_state = 'ROTATION'
    else:
        regime = 'CONSOLIDATION'
        risk_state = 'NEUTRAL'

    vol_tier = 'HIGH_VOLATILITY' if vol_20d > 18.0 else ('LOW_VOLATILITY' if vol_20d < 12.0 else 'NORMAL_VOLATILITY')

    return {
        'regime': regime,
        'volatility_tier': vol_tier,
        'risk_state': risk_state,
        'ret_5d': round(ret_5d, 2),
        'ret_20d': round(ret_20d, 2),
        'vol_20d': round(vol_20d, 2)
    }

def evaluate_historical_analog_quality(
    current_state_row: pd.Series,
    df_history: pd.DataFrame,
    top_k: int = 10
) -> Dict[str, Any]:
    """
    Finds top_k closest historical industry states and calculates detailed quality metrics:
    - Average similarity
    - Return dispersion
    - Directional consistency (% positive)
    - P90 upside potential
    """
    curr_date = current_state_row['date']
    hist_pool = df_history[df_history['date'] < curr_date].copy()
    
    if len(hist_pool) < top_k:
        return {
            'analog_count': len(hist_pool),
            'avg_similarity': 50.0,
            'best_similarity': 50.0,
            'directional_consistency (%)': 50.0,
            'analog_median_return': 0.0,
            'analog_p90_return': 0.0,
            'analog_quality_score': 35.0,
            'analog_returns_20d': []
        }

    valid_cols = [c for c in ANALOG_FEATURE_COLS if c in hist_pool.columns and c in current_state_row]
    X_hist = hist_pool[valid_cols].fillna(50).values
    x_curr = current_state_row[valid_cols].fillna(50).values.reshape(1, -1)

    mean_h = np.mean(X_hist, axis=0)
    std_h = np.std(X_hist, axis=0)
    std_h[std_h == 0] = 1.0

    X_hist_std = (X_hist - mean_h) / std_h
    x_curr_std = (x_curr - mean_h) / std_h

    dists = cdist(x_curr_std, X_hist_std, metric='euclidean')[0]
    hist_pool['distance'] = dists
    analogs = hist_pool.sort_values('distance').head(top_k).copy()
    
    similarities = np.clip(100.0 - analogs['distance'] * 15.0, 10.0, 99.0)
    avg_sim = float(np.mean(similarities))
    best_sim = float(np.max(similarities))

    rets_20d = analogs['fwd_ret_20d'].dropna().tolist() if 'fwd_ret_20d' in analogs.columns else []
    if len(rets_20d) >= 3:
        dir_cons = float(np.mean(np.array(rets_20d) > 0) * 100.0)
        med_ret = float(np.median(rets_20d))
        p90_ret = float(np.percentile(rets_20d, 90))
    else:
        dir_cons = 50.0
        med_ret = 0.0
        p90_ret = 0.0

    # Composite Analog Quality Score
    quality_score = float(np.clip(
        0.40 * avg_sim +
        0.30 * dir_cons +
        0.30 * np.clip(p90_ret * 3.0 + 50.0, 10.0, 99.0),
        15.0, 95.0
    ))

    return {
        'analog_count': len(analogs),
        'avg_similarity': round(avg_sim, 1),
        'best_similarity': round(best_sim, 1),
        'directional_consistency (%)': round(dir_cons, 1),
        'analog_median_return': round(med_ret, 2),
        'analog_p90_return': round(p90_ret, 2),
        'analog_quality_score': round(quality_score, 1),
        'analog_returns_20d': rets_20d
    }

def compute_model_consensus(
    model_predictions: Dict[str, float]
) -> Tuple[float, str]:
    """
    Evaluates forecast convergence across independent architectures:
    (Factor Model, Ridge, Elastic Net, Quantile Regression, Historical Analogs, Regime Model).
    """
    preds = list(model_predictions.values())
    if not preds or len(preds) < 3:
        return 50.0, 'MODERATE_CONSENSUS'

    mean_pred = np.mean(preds)
    std_pred = np.std(preds)

    # Standard deviation < 0.60% -> High consensus; > 1.80% -> High divergence
    consensus_score = float(np.clip(100.0 - std_pred * 25.0, 10.0, 98.0))

    if consensus_score >= 80.0:
        label = 'HIGH MODEL CONSENSUS'
    elif consensus_score >= 60.0:
        label = 'MODERATE CONSENSUS'
    else:
        label = 'MODEL DIVERGENCE / DISAGREEMENT'

    return round(consensus_score, 1), label
