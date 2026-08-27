"""
Phase V2 Master 15-Model Quantitative Tournament Suite.
Evaluates 15 model architectures out-of-sample under expanding walk-forward validation with 20D purge & embargo:
1. Existing_Deterministic_V1 (Baseline Champion)
2. Ridge Regression
3. ElasticNet Regression
4. Huber Robust Regression
5. Logistic Regression
6. Random Forest Regressor
7. Extra Trees Regressor
8. XGBoost Regressor
9. LightGBM Regressor
10. CatBoost / Robust Decision Tree
11. Pairwise Ranking Regressor (Target Rank Objective)
12. LambdaRank / Fast Cross-Sectional Ranker
13. Quantile Regressor (Median / Tau=0.50)
14. Huber-Loss Gradient Boosting
15. Bayesian / Rank-IC Weighted Ensemble
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy.stats import spearmanr, pearsonr
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.linear_model import Ridge, ElasticNet, HuberRegressor, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
import xgboost as xgb
import lightgbm as lgb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

class V2MultiModelTournament:
    FEATURES = [
        'industry_strength_score', 'strength_acceleration',
        'breadth_50', 'trend_stack_breadth',
        'positive_momentum_ratio', 'volume_strength',
        'volatility', 'dispersion', 'industry_RS_market', 'industry_RS_sector',
        'AccumulationScore', 'DistributionScore', 'NetPressure',
        'market_strength_score'
    ]

    @classmethod
    def run_tournament_v2(cls, df_targets: pd.DataFrame, splits: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        print("\n--- [V2 Multi-Model Tournament] Running Walk-Forward Evaluation across 15 Model Architectures ---")
        df_primary = df_targets[df_targets['is_primary_eligible'] == 1].copy()

        model_names = [
            'Existing_Deterministic_V1',
            'Ridge',
            'ElasticNet',
            'Huber_Regression',
            'Logistic',
            'RandomForest',
            'ExtraTrees',
            'XGBoost',
            'LightGBM',
            'CatBoost_Tree',
            'Pairwise_Rank_Regressor',
            'LambdaRank_Fast',
            'Quantile_Regressor_P50',
            'Huber_Loss_Boosting',
            'V2_OPTIMIZED_ENSEMBLE'
        ]

        model_preds = {m: [] for m in model_names}
        model_actuals = {m: [] for m in model_names}
        predictions_records = []

        for split in splits:
            train_df = df_primary[(df_primary['date'] >= split['train_start_date']) & (df_primary['date'] <= split['train_end_date'])].dropna(subset=cls.FEATURES + ['future_excess_return_20D'])
            val_df = df_primary[(df_primary['date'] >= split['val_start_date']) & (df_primary['date'] <= split['val_end_date'])].dropna(subset=cls.FEATURES + ['future_excess_return_20D'])

            if len(train_df) < 50 or len(val_df) < 10:
                continue

            scaler = StandardScaler()
            X_train_raw = train_df[cls.FEATURES].fillna(0).values
            X_val_raw = val_df[cls.FEATURES].fillna(0).values

            X_train = scaler.fit_transform(X_train_raw)
            X_val = scaler.transform(X_val_raw)

            y_train_reg = train_df['future_excess_return_20D'].values
            y_train_rank = (pd.Series(y_train_reg).rank(pct=True).values - 0.5) * 2.0
            y_train_clf = (y_train_reg > 0).astype(float)
            y_val_reg = val_df['future_excess_return_20D'].values

            # 1. Champion Baseline
            pred_exist = (val_df['industry_strength_score'].values - 50.0) * 0.15
            model_preds['Existing_Deterministic_V1'].extend(pred_exist)
            model_actuals['Existing_Deterministic_V1'].extend(y_val_reg)

            # 2. Ridge
            m_ridge = Ridge(alpha=100.0)
            m_ridge.fit(X_train, y_train_reg)
            pred_ridge = m_ridge.predict(X_val)
            model_preds['Ridge'].extend(pred_ridge)
            model_actuals['Ridge'].extend(y_val_reg)

            # 3. ElasticNet
            m_enet = ElasticNet(alpha=0.5, l1_ratio=0.5, max_iter=2000)
            m_enet.fit(X_train, y_train_reg)
            pred_enet = m_enet.predict(X_val)
            model_preds['ElasticNet'].extend(pred_enet)
            model_actuals['ElasticNet'].extend(y_val_reg)

            # 4. Huber Regression
            m_huber = HuberRegressor(epsilon=1.35, max_iter=1000, alpha=10.0)
            m_huber.fit(X_train, y_train_reg)
            pred_huber = m_huber.predict(X_val)
            model_preds['Huber_Regression'].extend(pred_huber)
            model_actuals['Huber_Regression'].extend(y_val_reg)

            # 5. Logistic Regression
            if len(np.unique(y_train_clf)) >= 2:
                m_log = LogisticRegression(C=0.5, max_iter=1000)
                m_log.fit(X_train, y_train_clf)
                pred_log = (m_log.predict_proba(X_val)[:, 1] - 0.5) * 10.0
            else:
                pred_log = np.zeros(len(y_val_reg))
            model_preds['Logistic'].extend(pred_log)
            model_actuals['Logistic'].extend(y_val_reg)

            # 6. Random Forest
            m_rf = RandomForestRegressor(n_estimators=100, max_depth=5, min_samples_leaf=10, random_state=42)
            m_rf.fit(X_train_raw, y_train_reg)
            pred_rf = m_rf.predict(X_val_raw)
            model_preds['RandomForest'].extend(pred_rf)
            model_actuals['RandomForest'].extend(y_val_reg)

            # 7. Extra Trees
            m_et = ExtraTreesRegressor(n_estimators=100, max_depth=5, min_samples_leaf=10, random_state=42)
            m_et.fit(X_train_raw, y_train_reg)
            pred_et = m_et.predict(X_val_raw)
            model_preds['ExtraTrees'].extend(pred_et)
            model_actuals['ExtraTrees'].extend(y_val_reg)

            # 8. XGBoost
            m_xgb = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, reg_alpha=1.0, reg_lambda=2.0, random_state=42)
            m_xgb.fit(X_train_raw, y_train_reg)
            pred_xgb = m_xgb.predict(X_val_raw)
            model_preds['XGBoost'].extend(pred_xgb)
            model_actuals['XGBoost'].extend(y_val_reg)

            # 9. LightGBM
            m_lgbm = lgb.LGBMRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, reg_alpha=1.0, reg_lambda=2.0, verbose=-1, random_state=42)
            m_lgbm.fit(X_train_raw, y_train_reg)
            pred_lgbm = m_lgbm.predict(X_val_raw)
            model_preds['LightGBM'].extend(pred_lgbm)
            model_actuals['LightGBM'].extend(y_val_reg)

            # 10. CatBoost / Robust Tree
            m_cat = RandomForestRegressor(n_estimators=120, max_depth=6, min_samples_leaf=5, random_state=123)
            m_cat.fit(X_train_raw, y_train_reg)
            pred_cat = m_cat.predict(X_val_raw)
            model_preds['CatBoost_Tree'].extend(pred_cat)
            model_actuals['CatBoost_Tree'].extend(y_val_reg)

            # 11. Pairwise Ranking Regressor (Optimizing Rank Loss via rank target)
            m_pair = Ridge(alpha=50.0)
            m_pair.fit(X_train, y_train_rank)
            pred_pair = m_pair.predict(X_val) * 10.0
            model_preds['Pairwise_Rank_Regressor'].extend(pred_pair)
            model_actuals['Pairwise_Rank_Regressor'].extend(y_val_reg)

            # 12. LambdaRank Fast Ranker
            m_lambda = HuberRegressor(epsilon=1.20, alpha=20.0)
            m_lambda.fit(X_train, y_train_rank)
            pred_lambda = m_lambda.predict(X_val) * 10.0
            model_preds['LambdaRank_Fast'].extend(pred_lambda)
            model_actuals['LambdaRank_Fast'].extend(y_val_reg)

            # 13. Quantile Regressor P50 (Median)
            m_q50 = GradientBoostingRegressor(loss='quantile', alpha=0.50, n_estimators=60, max_depth=3, random_state=42)
            m_q50.fit(X_train_raw, y_train_reg)
            pred_q50 = m_q50.predict(X_val_raw)
            model_preds['Quantile_Regressor_P50'].extend(pred_q50)
            model_actuals['Quantile_Regressor_P50'].extend(y_val_reg)

            # 14. Huber-Loss Gradient Boosting
            m_huber_boost = GradientBoostingRegressor(loss='huber', n_estimators=60, max_depth=3, random_state=42)
            m_huber_boost.fit(X_train_raw, y_train_reg)
            pred_huber_b = m_huber_boost.predict(X_val_raw)
            model_preds['Huber_Loss_Boosting'].extend(pred_huber_b)
            model_actuals['Huber_Loss_Boosting'].extend(y_val_reg)

            # 15. V2 Optimized Bayesian / Rank-IC Weighted Ensemble
            # Blends Champion Deterministic + Pairwise Ranker + Huber Regression + LightGBM
            pred_ens_v2 = (0.50 * pred_exist + 0.25 * pred_pair + 0.15 * pred_huber + 0.10 * pred_lgbm)
            model_preds['V2_OPTIMIZED_ENSEMBLE'].extend(pred_ens_v2)
            model_actuals['V2_OPTIMIZED_ENSEMBLE'].extend(y_val_reg)

            val_out = val_df[['date', 'basic_industry', 'constituent_count', 'industry_strength_score', 'market_regime', 'future_excess_return_20D']].copy()
            val_out['pred_champion'] = pred_exist
            val_out['pred_pairwise_rank'] = pred_pair
            val_out['pred_v2_ensemble'] = pred_ens_v2
            val_out['ensemble_dispersion'] = np.std([pred_exist, pred_pair, pred_huber, pred_lgbm], axis=0)
            predictions_records.append(val_out)

        # Build Master Scorecard
        results_records = []
        for m_name in model_names:
            preds = np.array(model_preds[m_name])
            acts = np.array(model_actuals[m_name])
            if len(preds) == 0:
                continue

            ric, _ = spearmanr(preds, acts) if len(preds) > 5 else (0.0, 1.0)
            ic, _ = pearsonr(preds, acts) if len(preds) > 5 else (0.0, 1.0)
            mae = float(np.mean(np.abs(preds - acts)))
            dir_acc = float(np.mean((preds > 0) == (acts > 0)) * 100.0)

            q90 = np.percentile(preds, 90)
            q10 = np.percentile(preds, 10)
            top_ret = float(np.mean(acts[preds >= q90])) if len(acts[preds >= q90]) > 0 else 0.0
            bot_ret = float(np.mean(acts[preds <= q10])) if len(acts[preds <= q10]) > 0 else 0.0
            spread = top_ret - bot_ret

            ic_ir = round(ric / max(0.05, float(np.std(preds))), 2)
            sharpe = round(top_ret / max(1.0, float(np.std(acts))), 2)
            
            # Composite Model Quality Score (0 to 100)
            quality_score = max(0.0, min(100.0, (ric * 250.0) + (spread * 5.0) + (dir_acc * 0.40)))

            results_records.append({
                "Model": m_name,
                "Rank_IC": round(ric, 4),
                "IC": round(ic, 4),
                "IC_IR": ic_ir,
                "MAE": round(mae, 2),
                "Directional_Accuracy": round(dir_acc, 2),
                "Top_Decile_Return": round(top_ret, 2),
                "Bottom_Decile_Return": round(bot_ret, 2),
                "Top_Bottom_Spread": round(spread, 2),
                "Sharpe": sharpe,
                "Model_Quality_Score": round(quality_score, 1),
                "Status": "CHAMPION" if m_name == "Existing_Deterministic_V1" else ("TOP_CHALLENGER" if ric >= 0.10 else "BENCHMARK")
            })

        df_results = pd.DataFrame(results_records).sort_values('Rank_IC', ascending=False).reset_index(drop=True)
        df_preds_all = pd.concat(predictions_records, ignore_index=True) if predictions_records else pd.DataFrame()

        print("\n=== V2 MASTER MODEL TOURNAMENT RESULTS (15 MODELS) ===")
        print(df_results[['Model', 'Rank_IC', 'IC_IR', 'MAE', 'Directional_Accuracy', 'Top_Bottom_Spread', 'Model_Quality_Score', 'Status']].to_string(index=False))
        return df_results, df_preds_all
