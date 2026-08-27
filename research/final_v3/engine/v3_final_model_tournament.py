"""
Final V3 Production Research 8-Model Tournament Engine.
Evaluates 8 candidate models out-of-sample across walk-forward splits with 20D purge & embargo:
1. Existing_Deterministic_V1 (Control Benchmark)
2. Final_Deterministic_Enhanced
3. Regime_Adaptive_Champion
4. Probability_Calibrated_Champion
5. ML_Residual_Challenger
6. Quantile_Challenger
7. Ranking_Challenger
8. Final_Hybrid_Challenger
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy.stats import spearmanr, pearsonr
from sklearn.linear_model import Ridge, HuberRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

class V3FinalModelTournament:
    FEATURES = [
        'industry_strength_score', 'strength_acceleration',
        'BREADTH_50', 'trend_stack_breadth',
        'positive_momentum_ratio', 'volume_strength',
        'volatility', 'dispersion', 'industry_RS_market',
        'AccumulationScore', 'DistributionScore', 'NetPressure',
        'market_strength_score'
    ]

    @classmethod
    def run_tournament_final_v3(cls, df_targets: pd.DataFrame, splits: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        print("\n--- [Final V3 Model Tournament] Running Walk-Forward Cross-Validation across 8 Candidates ---")
        df_primary = df_targets[df_targets['is_primary_eligible'] == 1].copy()

        models = [
            'Existing_Deterministic_V1',
            'Final_Deterministic_Enhanced',
            'Regime_Adaptive_Champion',
            'Probability_Calibrated_Champion',
            'ML_Residual_Challenger',
            'Quantile_Challenger',
            'Ranking_Challenger',
            'Final_Hybrid_Challenger'
        ]

        preds_dict = {m: [] for m in models}
        acts_dict = {m: [] for m in models}
        preds_records = []

        for split in splits:
            train_df = df_primary[(df_primary['date'] >= split['train_start_date']) & (df_primary['date'] <= split['train_end_date'])].dropna(subset=cls.FEATURES + ['future_excess_return_20D'])
            val_df = df_primary[(df_primary['date'] >= split['val_start_date']) & (df_primary['date'] <= split['val_end_date'])].dropna(subset=cls.FEATURES + ['future_excess_return_20D'])

            if len(train_df) < 50 or len(val_df) < 10:
                continue

            X_train = train_df[cls.FEATURES].fillna(0).values
            X_val = val_df[cls.FEATURES].fillna(0).values
            y_train = train_df['future_excess_return_20D'].values
            y_train_rank = (pd.Series(y_train).rank(pct=True).values - 0.5) * 2.0
            y_val = val_df['future_excess_return_20D'].values

            # 1. Existing_Deterministic_V1 (Control)
            p_exist = (val_df['industry_strength_score'].values - 50.0) * 0.15
            preds_dict['Existing_Deterministic_V1'].extend(p_exist)
            acts_dict['Existing_Deterministic_V1'].extend(y_val)

            # 2. Final_Deterministic_Enhanced
            p_enh = (val_df['industry_strength_score'].values - 50.0) * 0.15 + val_df['strength_acceleration'].values.clip(-10, 10) * 0.05
            preds_dict['Final_Deterministic_Enhanced'].extend(p_enh)
            acts_dict['Final_Deterministic_Enhanced'].extend(y_val)

            # 3. Regime_Adaptive_Champion
            p_reg = p_exist * val_df['REGIME_SIGNAL_MULTIPLIER'].fillna(1.0).values
            preds_dict['Regime_Adaptive_Champion'].extend(p_reg)
            acts_dict['Regime_Adaptive_Champion'].extend(y_val)

            # 4. Probability_Calibrated_Champion
            p_cal = p_exist * (val_df['CONFIDENCE_SCORE'].fillna(50.0).values / 50.0)
            preds_dict['Probability_Calibrated_Champion'].extend(p_cal)
            acts_dict['Probability_Calibrated_Champion'].extend(y_val)

            # 5. ML_Residual_Challenger (Huber Regressor on Residuals)
            m_res = HuberRegressor(epsilon=1.35, alpha=20.0)
            m_res.fit(X_train, y_train)
            p_ml_res = m_res.predict(X_val)
            preds_dict['ML_Residual_Challenger'].extend(p_ml_res)
            acts_dict['ML_Residual_Challenger'].extend(y_val)

            # 6. Quantile_Challenger (Median Gradient Boost)
            m_q = GradientBoostingRegressor(loss='quantile', alpha=0.50, n_estimators=50, max_depth=3, random_state=42)
            m_q.fit(X_train, y_train)
            p_q = m_q.predict(X_val)
            preds_dict['Quantile_Challenger'].extend(p_q)
            acts_dict['Quantile_Challenger'].extend(y_val)

            # 7. Ranking_Challenger (Ridge on Rank Target)
            m_rank = Ridge(alpha=50.0)
            m_rank.fit(X_train, y_train_rank)
            p_rank = m_rank.predict(X_val) * 10.0
            preds_dict['Ranking_Challenger'].extend(p_rank)
            acts_dict['Ranking_Challenger'].extend(y_val)

            # 8. Final_Hybrid_Challenger
            p_hyb = (0.60 * p_exist + 0.20 * p_reg + 0.20 * p_rank)
            preds_dict['Final_Hybrid_Challenger'].extend(p_hyb)
            acts_dict['Final_Hybrid_Challenger'].extend(y_val)

            val_out = val_df[['date', 'basic_industry', 'constituent_count', 'industry_strength_score', 'REGIME', 'future_excess_return_20D']].copy()
            val_out['pred_existing_v1'] = p_exist
            val_out['pred_final_hybrid'] = p_hyb
            preds_records.append(val_out)

        # Scorecard Generation
        results_records = []
        for m in models:
            preds = np.array(preds_dict[m])
            acts = np.array(acts_dict[m])
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
            sharpe = round(top_ret / max(1.0, float(np.std(acts))), 2)

            results_records.append({
                "Model": m,
                "Rank_IC": round(ric, 4),
                "IC": round(ic, 4),
                "IC_IR": round(ric / max(0.05, float(np.std(preds))), 2),
                "MAE": round(mae, 2),
                "Directional_Accuracy": round(dir_acc, 2),
                "Top_Decile_Return": round(top_ret, 2),
                "Bottom_Decile_Return": round(bot_ret, 2),
                "Top_Bottom_Spread": round(spread, 2),
                "Sharpe": sharpe,
                "Status": "CHAMPION" if m == "Existing_Deterministic_V1" else ("CHALLENGER" if ric >= 0.08 else "REJECTED")
            })

        df_res = pd.DataFrame(results_records).sort_values('Rank_IC', ascending=False).reset_index(drop=True)
        df_preds_all = pd.concat(preds_records, ignore_index=True) if preds_records else pd.DataFrame()

        print("\n=== FINAL V3 MODEL TOURNAMENT SCORECARD (8 CANDIDATES) ===")
        print(df_res[['Model', 'Rank_IC', 'IC_IR', 'MAE', 'Directional_Accuracy', 'Top_Bottom_Spread', 'Sharpe', 'Status']].to_string(index=False))
        return df_res, df_preds_all
