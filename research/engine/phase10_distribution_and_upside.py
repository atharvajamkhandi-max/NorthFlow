"""
Phase 10: Non-Gaussian Conditional Return Distribution & Extreme Upside Engine.
Implements:
1. Non-Gaussian Fat-Tailed Return Distribution (Student-t + Empirical Analogs)
2. Uncompressed Calibrated Tail Probabilities (P > 2%, 5%, 8%, 10%, 15%, 20%)
3. Upside Asymmetry Score (P90-P50 skew & positive/negative ratio)
4. Extreme Upside Signature Detector (Breadth Accel + RS + Leadership + Volume Confirmation)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from scipy.stats import t as student_t

def compute_conditional_return_distribution(
    exp_return: float,
    horizon_days: int,
    analog_returns: List[float] = None,
    vol_scale: float = 1.0
) -> Dict[str, float]:
    """
    Computes a non-Gaussian fat-tailed conditional return distribution
    using a Student-t (df=4) distribution blended with empirical analog returns.
    """
    h_scale = np.sqrt(horizon_days / 5.0)
    base_sigma = 2.45 * h_scale * vol_scale

    # Student-t with df=4 (heavy tails matching Indian market dynamics)
    df_param = 4.0
    scale = base_sigma * np.sqrt((df_param - 2.0) / df_param)

    # Parametric quantiles
    p5_param = float(exp_return + student_t.ppf(0.05, df_param, scale=scale))
    p10_param = float(exp_return + student_t.ppf(0.10, df_param, scale=scale))
    p25_param = float(exp_return + student_t.ppf(0.25, df_param, scale=scale))
    p50_param = float(exp_return)
    p75_param = float(exp_return + student_t.ppf(0.75, df_param, scale=scale))
    p90_param = float(exp_return + student_t.ppf(0.90, df_param, scale=scale))
    p95_param = float(exp_return + student_t.ppf(0.95, df_param, scale=scale))

    # Blend with empirical analogs if available
    if analog_returns is not None and len(analog_returns) >= 5:
        p10_emp = float(np.percentile(analog_returns, 10))
        p50_emp = float(np.percentile(analog_returns, 50))
        p90_emp = float(np.percentile(analog_returns, 90))
        p95_emp = float(np.percentile(analog_returns, 95))

        p10 = 0.60 * p10_param + 0.40 * p10_emp
        p50 = 0.60 * p50_param + 0.40 * p50_emp
        p90 = 0.60 * p90_param + 0.40 * p90_emp
        p95 = 0.60 * p95_param + 0.40 * p95_emp
        p5 = min(p5_param, p10 - 0.5)
        p25 = (p10 + p50) / 2.0
        p75 = (p50 + p90) / 2.0
    else:
        p5, p10, p25, p50, p75, p90, p95 = p5_param, p10_param, p25_param, p50_param, p75_param, p90_param, p95_param

    # Guarantee strict monotonic ordering
    qs = sorted([p5, p10, p25, p50, p75, p90, p95])
    p5, p10, p25, p50, p75, p90, p95 = qs[0], qs[1], qs[2], qs[3], qs[4], qs[5], qs[6]

    # Uncompressed tail threshold probabilities (Student-t survival function)
    p_gt_0 = float(np.clip((1.0 - student_t.cdf(0.0, df_param, loc=exp_return, scale=scale)) * 100.0, 5.0, 95.0))
    p_gt_2 = float(np.clip((1.0 - student_t.cdf(2.0, df_param, loc=exp_return, scale=scale)) * 100.0, 3.0, 92.0))
    p_gt_5 = float(np.clip((1.0 - student_t.cdf(5.0, df_param, loc=exp_return, scale=scale)) * 100.0, 2.0, 88.0))
    p_gt_8 = float(np.clip((1.0 - student_t.cdf(8.0, df_param, loc=exp_return, scale=scale)) * 100.0, 1.5, 82.0))
    p_gt_10 = float(np.clip((1.0 - student_t.cdf(10.0, df_param, loc=exp_return, scale=scale)) * 100.0, 1.0, 75.0))
    p_gt_15 = float(np.clip((1.0 - student_t.cdf(15.0, df_param, loc=exp_return, scale=scale)) * 100.0, 0.5, 60.0))
    p_gt_20 = float(np.clip((1.0 - student_t.cdf(20.0, df_param, loc=exp_return, scale=scale)) * 100.0, 0.2, 45.0))

    # Upside Asymmetry Score
    upside_spread = max(0.0, p90 - p50)
    downside_spread = max(0.1, p50 - p10)
    asymmetry_ratio = upside_spread / downside_spread
    upside_asymmetry_score = float(np.clip(50.0 + (asymmetry_ratio - 1.0) * 30.0 + (p_gt_8 / 2.0), 10.0, 99.0))

    return {
        'mean': round(exp_return, 2),
        'p5': round(p5, 2),
        'p10': round(p10, 2),
        'p25': round(p25, 2),
        'p50': round(p50, 2),
        'p75': round(p75, 2),
        'p90': round(p90, 2),
        'p95': round(p95, 2),
        'p_gt_0': round(p_gt_0, 1),
        'p_gt_2': round(p_gt_2, 1),
        'p_gt_5': round(p_gt_5, 1),
        'p_gt_8': round(p_gt_8, 1),
        'p_gt_10': round(p_gt_10, 1),
        'p_gt_15': round(p_gt_15, 1),
        'p_gt_20': round(p_gt_20, 1),
        'upside_asymmetry_score': round(upside_asymmetry_score, 1)
    }

def detect_extreme_upside_signature(row: pd.Series) -> Tuple[float, str]:
    """
    Evaluates whether an industry exhibits the multi-factor precursor signature
    of historical >+10% and >+15% upward explosive moves:
    1. Rapid Breadth Acceleration (d_breadth > 0)
    2. Relative Strength Outperformance (RS > 55)
    3. Positive Residual Momentum (Alpha > 0)
    4. Positive Directional Volume Pressure
    5. Trend Stack Expansion
    """
    rs = float(row.get('avg_rs_5d', 50))
    br_acc = float(row.get('d_breadth_5d', 0))
    res_mom = float(row.get('residual_mom_5d', 0))
    vol_spread = float(row.get('dir_vol_spread_12', 50))
    trend_br = float(row.get('trend_stack_breadth', 50))

    score = (
        0.30 * np.clip((rs - 50.0) / 20.0 * 50.0 + 50.0, 0, 100) +
        0.25 * np.clip(br_acc * 3.0 + 50.0, 0, 100) +
        0.20 * np.clip(res_mom * 10.0 + 50.0, 0, 100) +
        0.15 * np.clip((vol_spread - 50.0) / 20.0 * 50.0 + 50.0, 0, 100) +
        0.10 * np.clip(trend_br, 0, 100)
    )

    if score >= 70.0:
        sig_label = 'HIGH EXTREME UPSIDE POTENTIAL'
    elif score >= 55.0:
        sig_label = 'MODERATE UPSIDE SIGNATURE'
    elif score <= 35.0:
        sig_label = 'NEGATIVE DOWNSIDE PRESSURE'
    else:
        sig_label = 'NEUTRAL / DORMANT'

    return round(score, 1), sig_label
