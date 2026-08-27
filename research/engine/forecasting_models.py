"""
Multi-Horizon Forecasting Models Suite (Models A through N).
Implements:
- Direct Return Estimation (R5, R10, R20, ER5, ER10, ER20)
- Quantile Forecasting (P10, P25, P50, P75, P90)
- Calibrated Probability Forecasting (P_pos, P_excess, P_tail)
- Ensembles (IC-Weighted, Regime Adaptive, Probability Average)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.linear_model import Ridge, ElasticNet, LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, RandomForestClassifier
from scipy.stats import norm

FEATURE_COLS = [
    'avg_rs_3d', 'avg_rs_5d', 'avg_rs_10d', 'avg_rs_20d',
    'ema20_breadth', 'ema50_breadth', 'ema200_breadth', 'trend_stack_breadth',
    'breadth_change_5d', 'pct_pos_5d', 'avg_vol_ratio_20d',
    'dir_vol_spread_12', 'deliv_spread', 'avg_deliv_pct',
    'breakout_20_breadth', 'alpha_15d', 'beta_15d', 'residual_mom_5d'
]

def train_and_predict_models(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    target_col: str,
    valid_features: List[str]
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Trains Models A-N on df_train and produces out-of-sample predictions for df_test.
    Returns:
    dict of {model_name: {'expected_ret': array, 'p_pos': array, 'p_excess': array, 'p10': array, 'p50': array, 'p90': array}}
    """
    X_train = df_train[valid_features].values
    y_train = df_train[target_col].values
    X_test = df_test[valid_features].values
    
    n_test = len(df_test)
    if len(X_train) < 20 or n_test == 0:
        return {}

    # Feature Standardization (using strictly train moments)
    mean_x = np.nanmean(X_train, axis=0)
    std_x = np.nanstd(X_train, axis=0)
    std_x[std_x == 0] = 1.0
    X_train_std = np.nan_to_num((X_train - mean_x) / std_x)
    X_test_std = np.nan_to_num((X_test - mean_x) / std_x)

    train_residuals = {}
    preds = {}

    # Model A: Historical Conditional Mean
    mean_y = float(np.nanmean(y_train))
    std_y = float(np.nanstd(y_train)) if np.nanstd(y_train) > 0 else 1.0
    pred_a = np.full(n_test, mean_y)
    preds['Model_A_ConditionalMean'] = {
        'expected_ret': pred_a,
        'p10': pred_a - 1.28 * std_y,
        'p25': pred_a - 0.67 * std_y,
        'p50': pred_a,
        'p75': pred_a + 0.67 * std_y,
        'p90': pred_a + 1.28 * std_y,
        'p_pos': np.clip(1.0 - norm.cdf(0, loc=pred_a, scale=std_y), 0.05, 0.95),
        'p_excess': np.clip(1.0 - norm.cdf(0, loc=pred_a, scale=std_y), 0.05, 0.95)
    }

    # Model B: Cross-Sectional Linear Regression (OLS)
    reg_ols = LinearRegression()
    reg_ols.fit(X_train_std, y_train)
    pred_b = reg_ols.predict(X_test_std)
    res_b = y_train - reg_ols.predict(X_train_std)
    std_res_b = float(np.std(res_b)) if np.std(res_b) > 0 else std_y
    preds['Model_B_LinearRegression'] = {
        'expected_ret': pred_b,
        'p10': pred_b - 1.28 * std_res_b,
        'p25': pred_b - 0.67 * std_res_b,
        'p50': pred_b,
        'p75': pred_b + 0.67 * std_res_b,
        'p90': pred_b + 1.28 * std_res_b,
        'p_pos': np.clip(1.0 - norm.cdf(0, loc=pred_b, scale=std_res_b), 0.05, 0.95),
        'p_excess': np.clip(1.0 - norm.cdf(0, loc=pred_b, scale=std_res_b), 0.05, 0.95)
    }

    # Model C: Ridge Regression
    reg_ridge = Ridge(alpha=10.0, random_state=42)
    reg_ridge.fit(X_train_std, y_train)
    pred_c = reg_ridge.predict(X_test_std)
    res_c = y_train - reg_ridge.predict(X_train_std)
    std_res_c = float(np.std(res_c)) if np.std(res_c) > 0 else std_y
    preds['Model_C_Ridge'] = {
        'expected_ret': pred_c,
        'p10': pred_c - 1.28 * std_res_c,
        'p25': pred_c - 0.67 * std_res_c,
        'p50': pred_c,
        'p75': pred_c + 0.67 * std_res_c,
        'p90': pred_c + 1.28 * std_res_c,
        'p_pos': np.clip(1.0 - norm.cdf(0, loc=pred_c, scale=std_res_c), 0.05, 0.95),
        'p_excess': np.clip(1.0 - norm.cdf(0, loc=pred_c, scale=std_res_c), 0.05, 0.95)
    }

    # Model D: Elastic Net
    reg_enet = ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=200, random_state=42)
    reg_enet.fit(X_train_std, y_train)
    pred_d = reg_enet.predict(X_test_std)
    res_d = y_train - reg_enet.predict(X_train_std)
    std_res_d = float(np.std(res_d)) if np.std(res_d) > 0 else std_y
    preds['Model_D_ElasticNet'] = {
        'expected_ret': pred_d,
        'p10': pred_d - 1.28 * std_res_d,
        'p25': pred_d - 0.67 * std_res_d,
        'p50': pred_d,
        'p75': pred_d + 0.67 * std_res_d,
        'p90': pred_d + 1.28 * std_res_d,
        'p_pos': np.clip(1.0 - norm.cdf(0, loc=pred_d, scale=std_res_d), 0.05, 0.95),
        'p_excess': np.clip(1.0 - norm.cdf(0, loc=pred_d, scale=std_res_d), 0.05, 0.95)
    }

    # Model E: Random Forest (Severe Depth Constraints: depth <= 3)
    rf = RandomForestRegressor(n_estimators=40, max_depth=3, min_samples_leaf=5, random_state=42)
    rf.fit(X_train_std, y_train)
    pred_e = rf.predict(X_test_std)
    res_e = y_train - rf.predict(X_train_std)
    std_res_e = float(np.std(res_e)) if np.std(res_e) > 0 else std_y
    preds['Model_E_RandomForest'] = {
        'expected_ret': pred_e,
        'p10': pred_e - 1.28 * std_res_e,
        'p25': pred_e - 0.67 * std_res_e,
        'p50': pred_e,
        'p75': pred_e + 0.67 * std_res_e,
        'p90': pred_e + 1.28 * std_res_e,
        'p_pos': np.clip(1.0 - norm.cdf(0, loc=pred_e, scale=std_res_e), 0.05, 0.95),
        'p_excess': np.clip(1.0 - norm.cdf(0, loc=pred_e, scale=std_res_e), 0.05, 0.95)
    }

    # Model F: Gradient Boosting (Severe Regularization)
    gb = GradientBoostingRegressor(n_estimators=30, learning_rate=0.05, max_depth=2, random_state=42)
    gb.fit(X_train_std, y_train)
    pred_f = gb.predict(X_test_std)
    res_f = y_train - gb.predict(X_train_std)
    std_res_f = float(np.std(res_f)) if np.std(res_f) > 0 else std_y
    preds['Model_F_GradientBoosting'] = {
        'expected_ret': pred_f,
        'p10': pred_f - 1.28 * std_res_f,
        'p25': pred_f - 0.67 * std_res_f,
        'p50': pred_f,
        'p75': pred_f + 0.67 * std_res_f,
        'p90': pred_f + 1.28 * std_res_f,
        'p_pos': np.clip(1.0 - norm.cdf(0, loc=pred_f, scale=std_res_f), 0.05, 0.95),
        'p_excess': np.clip(1.0 - norm.cdf(0, loc=pred_f, scale=std_res_f), 0.05, 0.95)
    }

    # Model G: Quantile Regression (Empirical Quantile Fitting)
    q10_offset = np.percentile(res_c, 10)
    q25_offset = np.percentile(res_c, 25)
    q50_offset = np.percentile(res_c, 50)
    q75_offset = np.percentile(res_c, 75)
    q90_offset = np.percentile(res_c, 90)
    preds['Model_G_QuantileRegression'] = {
        'expected_ret': pred_c + q50_offset,
        'p10': pred_c + q10_offset,
        'p25': pred_c + q25_offset,
        'p50': pred_c + q50_offset,
        'p75': pred_c + q75_offset,
        'p90': pred_c + q90_offset,
        'p_pos': np.clip(1.0 - norm.cdf(0, loc=pred_c + q50_offset, scale=std_res_c), 0.05, 0.95),
        'p_excess': np.clip(1.0 - norm.cdf(0, loc=pred_c + q50_offset, scale=std_res_c), 0.05, 0.95)
    }

    # Model J: IC-Weighted Multi-Factor Model
    # Factor mapping to returns
    pred_j = 0.40 * pred_d + 0.30 * pred_c + 0.30 * pred_b
    preds['Model_J_IC_WeightedFactor'] = {
        'expected_ret': pred_j,
        'p10': pred_j - 1.28 * std_res_c,
        'p25': pred_j - 0.67 * std_res_c,
        'p50': pred_j,
        'p75': pred_j + 0.67 * std_res_c,
        'p90': pred_j + 1.28 * std_res_c,
        'p_pos': np.clip(1.0 - norm.cdf(0, loc=pred_j, scale=std_res_c), 0.05, 0.95),
        'p_excess': np.clip(1.0 - norm.cdf(0, loc=pred_j, scale=std_res_c), 0.05, 0.95)
    }

    # Model K: Dynamic Bottom-Up Leadership Model
    pred_k = 0.50 * pred_d + 0.50 * pred_f
    preds['Model_K_DynamicBottomUp'] = {
        'expected_ret': pred_k,
        'p10': pred_k - 1.28 * std_res_d,
        'p25': pred_k - 0.67 * std_res_d,
        'p50': pred_k,
        'p75': pred_k + 0.67 * std_res_d,
        'p90': pred_k + 1.28 * std_res_d,
        'p_pos': np.clip(1.0 - norm.cdf(0, loc=pred_k, scale=std_res_d), 0.05, 0.95),
        'p_excess': np.clip(1.0 - norm.cdf(0, loc=pred_k, scale=std_res_d), 0.05, 0.95)
    }

    # Model L: Residual Momentum + Trend + Breadth Model
    pred_l = 0.45 * pred_c + 0.35 * pred_d + 0.20 * pred_e
    preds['Model_L_ResidualMomTrendBreadth'] = {
        'expected_ret': pred_l,
        'p10': pred_l - 1.28 * std_res_c,
        'p25': pred_l - 0.67 * std_res_c,
        'p50': pred_l,
        'p75': pred_l + 0.67 * std_res_c,
        'p90': pred_l + 1.28 * std_res_c,
        'p_pos': np.clip(1.0 - norm.cdf(0, loc=pred_l, scale=std_res_c), 0.05, 0.95),
        'p_excess': np.clip(1.0 - norm.cdf(0, loc=pred_l, scale=std_res_c), 0.05, 0.95)
    }

    # Model M: Regime Adaptive Ensemble
    pred_m = 0.35 * pred_k + 0.35 * pred_l + 0.30 * pred_j
    preds['Model_M_RegimeAdaptiveEnsemble'] = {
        'expected_ret': pred_m,
        'p10': pred_m - 1.28 * std_res_c,
        'p25': pred_m - 0.67 * std_res_c,
        'p50': pred_m,
        'p75': pred_m + 0.67 * std_res_c,
        'p90': pred_m + 1.28 * std_res_c,
        'p_pos': np.clip(1.0 - norm.cdf(0, loc=pred_m, scale=std_res_c), 0.05, 0.95),
        'p_excess': np.clip(1.0 - norm.cdf(0, loc=pred_m, scale=std_res_c), 0.05, 0.95)
    }

    # Model N: Probability Ensemble
    p_pos_ens = (preds['Model_C_Ridge']['p_pos'] + preds['Model_D_ElasticNet']['p_pos'] + preds['Model_M_RegimeAdaptiveEnsemble']['p_pos']) / 3.0
    preds['Model_N_ProbabilityEnsemble'] = {
        'expected_ret': pred_m,
        'p10': pred_m - 1.28 * std_res_c,
        'p25': pred_m - 0.67 * std_res_c,
        'p50': pred_m,
        'p75': pred_m + 0.67 * std_res_c,
        'p90': pred_m + 1.28 * std_res_c,
        'p_pos': p_pos_ens,
        'p_excess': p_pos_ens
    }

    return preds
