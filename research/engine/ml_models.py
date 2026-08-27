"""
Machine Learning Quantitative Engine.
Implements Walk-Forward Purged Cross-Validation for:
- Logistic Regression
- Ridge Regression
- Elastic Net
- Random Forest
- Gradient Boosting
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
from sklearn.linear_model import LogisticRegression, Ridge, ElasticNet
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, brier_score_loss, mean_absolute_error, mean_squared_error, r2_score
from scipy.stats import spearmanr

FEATURE_COLS = [
    'avg_rs_3d', 'avg_rs_5d', 'avg_rs_10d', 'avg_rs_20d',
    'ema20_breadth', 'ema50_breadth', 'ema200_breadth', 'trend_stack_breadth',
    'breadth_change_5d', 'pct_pos_5d', 'avg_vol_ratio_20d',
    'avg_rsi_14', 'avg_deliv_pct', 'avg_risk_adj_5d', 'breakout_20_breadth',
    'alpha_15d', 'beta_15d', 'residual_mom_5d'
]

def run_ml_walk_forward_tournament(df_scored: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    df = df_scored.copy()
    if 'Y5' not in df.columns and 'Y_5d' in df.columns:
        df['Y5'] = df['Y_5d']
    if 'rel_fwd_5d' not in df.columns and 'rel_fwd_5d' in df.columns:
        df['rel_fwd_5d'] = df['rel_fwd_5d']

    df = df.dropna(subset=['Y5', 'rel_fwd_5d']).sort_values('date').copy()
    dates = sorted(df['date'].unique())
    
    if len(dates) < 12:
        return df, {"status": "INSUFFICIENT_WALK_FORWARD_DATES", "sessions": len(dates)}

    min_train_sessions = 8
    embargo_days = 5

    df['ML_Logistic_P5'] = np.nan
    df['ML_Ridge_Ret5'] = np.nan
    df['ML_ElasticNet_P5'] = np.nan
    df['ML_RandomForest_P5'] = np.nan
    df['ML_GradientBoosting_P5'] = np.nan
    df['ML_GradientBoosting_Ret5'] = np.nan

    valid_feature_cols = [c for c in FEATURE_COLS if c in df.columns]

    ml_metrics = {
        'Logistic_Regression': {'y_true': [], 'y_prob': [], 'y_pred': []},
        'Ridge_Regression': {'y_true': [], 'y_pred': []},
        'Elastic_Net': {'y_true': [], 'y_prob': [], 'y_pred': []},
        'Random_Forest': {'y_true': [], 'y_prob': [], 'y_pred': []},
        'Gradient_Boosting': {'y_true': [], 'y_prob': [], 'y_pred': [], 'ret_true': [], 'ret_pred': []}
    }

    for t_idx in range(min_train_sessions, len(dates)):
        test_date = dates[t_idx]
        train_end_idx = max(0, t_idx - embargo_days)
        if train_end_idx < 3:
            train_end_idx = t_idx - 1

        train_dates = dates[:train_end_idx]
        train_mask = df['date'].isin(train_dates)
        test_mask = df['date'] == test_date

        df_train = df[train_mask].dropna(subset=valid_feature_cols + ['Y5', 'rel_fwd_5d'])
        df_test = df[test_mask].dropna(subset=valid_feature_cols)

        if len(df_train) < 30 or len(df_test) == 0:
            continue

        test_idx = df_test.index

        X_train = df_train[valid_feature_cols].values
        y_train_cls = df_train['Y5'].values
        y_train_reg = df_train['rel_fwd_5d'].values

        X_test = df_test[valid_feature_cols].values
        y_test_cls = df_test['Y5'].values
        y_test_reg = df_test['rel_fwd_5d'].values

        mean_x = np.nanmean(X_train, axis=0)
        std_x = np.nanstd(X_train, axis=0)
        std_x[std_x == 0] = 1.0
        X_train_std = np.nan_to_num((X_train - mean_x) / std_x)
        X_test_std = np.nan_to_num((X_test - mean_x) / std_x)

        # 1. Logistic Regression
        clf_lr = LogisticRegression(C=0.1, max_iter=200, random_state=42)
        clf_lr.fit(X_train_std, y_train_cls)
        p_lr = clf_lr.predict_proba(X_test_std)[:, 1]
        df.loc[test_idx, 'ML_Logistic_P5'] = p_lr
        ml_metrics['Logistic_Regression']['y_true'].extend(y_test_cls)
        ml_metrics['Logistic_Regression']['y_prob'].extend(p_lr)
        ml_metrics['Logistic_Regression']['y_pred'].extend((p_lr >= 0.5).astype(int))

        # 2. Ridge Regression
        reg_ridge = Ridge(alpha=10.0, random_state=42)
        reg_ridge.fit(X_train_std, y_train_reg)
        pred_ridge = reg_ridge.predict(X_test_std)
        df.loc[test_idx, 'ML_Ridge_Ret5'] = pred_ridge
        ml_metrics['Ridge_Regression']['y_true'].extend(y_test_reg)
        ml_metrics['Ridge_Regression']['y_pred'].extend(pred_ridge)

        # 3. Elastic Net
        reg_enet = ElasticNet(alpha=0.1, l1_ratio=0.5, max_iter=200, random_state=42)
        reg_enet.fit(X_train_std, y_train_reg)
        pred_enet = reg_enet.predict(X_test_std)
        p_enet = 1.0 / (1.0 + np.exp(-np.clip(pred_enet, -10, 10)))
        df.loc[test_idx, 'ML_ElasticNet_P5'] = p_enet
        ml_metrics['Elastic_Net']['y_true'].extend(y_test_cls)
        ml_metrics['Elastic_Net']['y_prob'].extend(p_enet)
        ml_metrics['Elastic_Net']['y_pred'].extend((p_enet >= 0.5).astype(int))

        # 4. Random Forest
        rf_cls = RandomForestClassifier(n_estimators=50, max_depth=3, min_samples_leaf=5, random_state=42)
        rf_cls.fit(X_train_std, y_train_cls)
        p_rf = rf_cls.predict_proba(X_test_std)[:, 1]
        df.loc[test_idx, 'ML_RandomForest_P5'] = p_rf
        ml_metrics['Random_Forest']['y_true'].extend(y_test_cls)
        ml_metrics['Random_Forest']['y_prob'].extend(p_rf)
        ml_metrics['Random_Forest']['y_pred'].extend((p_rf >= 0.5).astype(int))

        # 5. Gradient Boosting
        gb_cls = GradientBoostingClassifier(n_estimators=40, learning_rate=0.05, max_depth=2, random_state=42)
        gb_cls.fit(X_train_std, y_train_cls)
        p_gb = gb_cls.predict_proba(X_test_std)[:, 1]
        df.loc[test_idx, 'ML_GradientBoosting_P5'] = p_gb

        gb_reg = GradientBoostingRegressor(n_estimators=40, learning_rate=0.05, max_depth=2, random_state=42)
        gb_reg.fit(X_train_std, y_train_reg)
        pred_gb_ret = gb_reg.predict(X_test_std)
        df.loc[test_idx, 'ML_GradientBoosting_Ret5'] = pred_gb_ret

        ml_metrics['Gradient_Boosting']['y_true'].extend(y_test_cls)
        ml_metrics['Gradient_Boosting']['y_prob'].extend(p_gb)
        ml_metrics['Gradient_Boosting']['y_pred'].extend((p_gb >= 0.5).astype(int))
        ml_metrics['Gradient_Boosting']['ret_true'].extend(y_test_reg)
        ml_metrics['Gradient_Boosting']['ret_pred'].extend(pred_gb_ret)

    results_summary = []
    for model_name, m_data in ml_metrics.items():
        if 'y_prob' in m_data and len(m_data['y_true']) > 0:
            yt = np.array(m_data['y_true'])
            yp = np.array(m_data['y_prob'])
            yp_lbl = np.array(m_data['y_pred'])
            
            acc = accuracy_score(yt, yp_lbl)
            auc = roc_auc_score(yt, yp) if len(np.unique(yt)) > 1 else 0.50
            f1 = f1_score(yt, yp_lbl, zero_division=0)
            brier = brier_score_loss(yt, yp)
            
            results_summary.append({
                'Model': model_name,
                'Task': 'Classification (P5)',
                'Accuracy': round(acc * 100.0, 1),
                'ROC_AUC': round(auc, 3),
                'F1_Score': round(f1, 3),
                'Brier_Score': round(brier, 3),
                'Observations': len(yt)
            })

        if 'ret_true' in m_data and len(m_data['ret_true']) > 0:
            rt = np.array(m_data['ret_true'])
            rp = np.array(m_data['ret_pred'])
            mae = mean_absolute_error(rt, rp)
            rmse = np.sqrt(mean_squared_error(rt, rp))
            r2 = r2_score(rt, rp)
            ic, _ = spearmanr(rt, rp)
            results_summary.append({
                'Model': f"{model_name} (Regression)",
                'Task': 'Return Prediction (5D)',
                'MAE': round(mae, 2),
                'RMSE': round(rmse, 2),
                'R2': round(r2, 4),
                'Rank_IC': round(ic if not np.isnan(ic) else 0.0, 3),
                'Observations': len(rt)
            })

    return df, {"status": "SUCCESS", "metrics_summary": pd.DataFrame(results_summary)}
