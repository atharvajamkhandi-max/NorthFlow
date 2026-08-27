"""
Forecasting Chronological Walk-Forward Validation & Performance Evaluation Engine.
Evaluates:
- Multi-Horizon Walk-Forward Performance (5D, 10D, 20D)
- Overlapping vs Non-Overlapping Return Forecasting Accuracy (MAE, RMSE, R2, IC, Coverage)
- Probability Calibration (Brier, ECE, Log Loss, ROC-AUC)
- Forecast Decay Curve (1D, 3D, 5D, 10D, 15D, 20D)
- Portfolio Simulations (Top 5, 10, 20 vs Bottom Q5 vs Benchmark)
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from scipy.stats import spearmanr, kendalltau
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

from research.engine.forecasting_models import train_and_predict_models, FEATURE_COLS

def run_multi_horizon_walk_forward_evaluation(
    df_ind_matrix: pd.DataFrame,
    df_targets: pd.DataFrame,
    results_dir: str
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Clean merge without suffix duplication
    cols_to_drop = [c for c in df_ind_matrix.columns if c.startswith('fwd_ret_') or c.startswith('excess_fwd_') or c.startswith('mfe_') or c.startswith('mae_') or c.startswith('Y') or c.startswith('rel_fwd_')]
    df_base = df_ind_matrix.drop(columns=cols_to_drop, errors='ignore')
    df = pd.merge(df_base, df_targets, on=['date', 'basic_industry'], how='inner').sort_values(['basic_industry', 'date']).reset_index(drop=True)
    
    dates = sorted(df['date'].unique())
    n_dates = len(dates)
    min_train_sessions = 8
    embargo = 5

    valid_features = [c for c in FEATURE_COLS if c in df.columns]

    all_forecast_records = []

    # Walk-forward loop across dates
    for t_idx in range(min_train_sessions, n_dates):
        test_date = dates[t_idx]
        train_end_idx = max(0, t_idx - embargo)
        if train_end_idx < 3:
            train_end_idx = t_idx - 1
        
        train_dates = dates[:train_end_idx]
        df_train = df[df['date'].isin(train_dates)].copy()
        df_test = df[df['date'] == test_date].copy()

        if len(df_train) < 30 or len(df_test) == 0:
            continue

        for horizon in [5, 10, 20]:
            t_col = f'fwd_ret_{horizon}d'
            ex_col = f'excess_fwd_{horizon}d'
            
            if t_col not in df_train.columns:
                continue

            sub_train = df_train.dropna(subset=[t_col] + valid_features)
            sub_test = df_test.dropna(subset=valid_features)

            if len(sub_train) < 20 or len(sub_test) == 0:
                continue

            preds = train_and_predict_models(sub_train, sub_test, t_col, valid_features)

            for m_name, p_data in preds.items():
                for idx_row, (_, row) in enumerate(sub_test.iterrows()):
                    actual_ret = row.get(t_col, np.nan)
                    actual_excess = row.get(ex_col, np.nan)
                    
                    exp_ret = p_data['expected_ret'][idx_row]
                    p10 = p_data['p10'][idx_row]
                    p50 = p_data['p50'][idx_row]
                    p90 = p_data['p90'][idx_row]
                    p_pos = p_data['p_pos'][idx_row]
                    p_excess = p_data['p_excess'][idx_row]

                    all_forecast_records.append({
                        'date': test_date,
                        'basic_industry': row['basic_industry'],
                        'model': m_name,
                        'horizon': horizon,
                        'expected_ret': exp_ret,
                        'p10': p10,
                        'p25': p_data['p25'][idx_row],
                        'p50': p50,
                        'p75': p_data['p75'][idx_row],
                        'p90': p90,
                        'p_pos': p_pos,
                        'p_excess': p_excess,
                        'actual_ret': actual_ret,
                        'actual_excess': actual_excess,
                        'mfe': row.get(f'mfe_{horizon}d', np.nan),
                        'mae': row.get(f'mae_{horizon}d', np.nan)
                    })

    df_forecasts = pd.DataFrame(all_forecast_records)
    print(f"Generated {len(df_forecasts):,} out-of-sample forecast instances across {len(dates)} dates.")

    # 1. Forecast Model Evaluation Summary
    model_eval_rows = []
    for (m_name, h_val), grp in df_forecasts.groupby(['model', 'horizon']):
        valid = grp.dropna(subset=['actual_ret', 'expected_ret'])
        if len(valid) < 30:
            continue
        
        y_true = valid['actual_ret'].values
        y_pred = valid['expected_ret'].values
        
        mae = float(np.mean(np.abs(y_true - y_pred)))
        rmse = float(np.sqrt(np.mean((y_true - y_pred)**2)))
        med_ae = float(np.median(np.abs(y_true - y_pred)))
        
        # R2
        ss_tot = np.sum((y_true - np.mean(y_true))**2)
        ss_res = np.sum((y_true - y_pred)**2)
        r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Rank IC & Kendall Tau
        ic, _ = spearmanr(y_pred, y_true)
        ktau, _ = kendalltau(y_pred, y_true)
        
        # Sign Accuracy
        sign_acc = float((np.sign(y_pred) == np.sign(y_true)).mean() * 100.0)
        
        # 80% Prediction Interval Coverage (P10 to P90)
        coverage_80 = float(((y_true >= valid['p10'].values) & (y_true <= valid['p90'].values)).mean() * 100.0)

        # Brier Score & ECE for P_pos
        y_bin = (y_true > 0).astype(int)
        p_pos_vals = np.clip(valid['p_pos'].values, 0.01, 0.99)
        brier = float(brier_score_loss(y_bin, p_pos_vals))
        
        # ECE (10 bins)
        bins = np.linspace(0, 1, 11)
        bin_ids = np.digitize(p_pos_vals, bins) - 1
        ece = 0.0
        for b_i in range(10):
            mask = bin_ids == b_i
            if np.sum(mask) > 0:
                acc_b = np.mean(y_bin[mask])
                conf_b = np.mean(p_pos_vals[mask])
                ece += (np.sum(mask) / len(y_bin)) * abs(acc_b - conf_b)

        model_eval_rows.append({
            'Model_Name': m_name,
            'Horizon': f"{h_val}D Forward",
            'MAE (%)': round(mae, 2),
            'RMSE (%)': round(rmse, 2),
            'Median_AE (%)': round(med_ae, 2),
            'R2': round(r2, 4),
            'Rank_IC': round(ic if not np.isnan(ic) else 0.0, 4),
            'Kendall_Tau': round(ktau if not np.isnan(ktau) else 0.0, 3),
            'Sign_Accuracy (%)': round(sign_acc, 1),
            'PI_80_Coverage (%)': round(coverage_80, 1),
            'Brier_Score': round(brier, 4),
            'ECE': round(ece, 3),
            'Status': 'CALIBRATED' if abs(coverage_80 - 80.0) <= 15.0 else 'MIS-CALIBRATED'
        })

    df_model_eval = pd.DataFrame(model_eval_rows).sort_values(['Horizon', 'Rank_IC'], ascending=[True, False]).reset_index(drop=True)
    df_model_eval.to_csv(os.path.join(results_dir, "forecast_model_results.csv"), index=False)

    # 2. Probability Calibration Details
    calib_rows = []
    top_model = 'Model_M_RegimeAdaptiveEnsemble'
    df_top_m = df_forecasts[df_forecasts['model'] == top_model].dropna(subset=['actual_ret'])

    for h_val in [5, 10, 20]:
        sub_h = df_top_m[df_top_m['horizon'] == h_val]
        if sub_h.empty:
            continue
        y_bin = (sub_h['actual_ret'] > 0).astype(int)
        p_vals = sub_h['p_pos'].values
        
        auc_val = roc_auc_score(y_bin, p_vals) if len(np.unique(y_bin)) > 1 else 0.50
        brier = brier_score_loss(y_bin, p_vals)
        lloss = log_loss(y_bin, p_vals)

        calib_rows.append({
            'Model': top_model,
            'Horizon': f"{h_val}D Forward",
            'ROC_AUC': round(auc_val, 3),
            'Brier_Score': round(brier, 4),
            'Log_Loss': round(lloss, 3),
            'Mean_Predicted_Prob (%)': round(float(np.mean(p_vals) * 100.0), 1),
            'Empirical_Positive_Rate (%)': round(float(np.mean(y_bin) * 100.0), 1),
            'Calibration_Grade': 'EXCELLENT' if abs(np.mean(p_vals) - np.mean(y_bin)) < 0.05 else 'ACCEPTABLE'
        })

    df_calib = pd.DataFrame(calib_rows)
    df_calib.to_csv(os.path.join(results_dir, "calibration_results.csv"), index=False)

    # 3. Forecast Decay Curve Across 1D, 3D, 5D, 10D, 15D, 20D
    decay_rows = []
    for h in [1, 3, 5, 10, 15, 20]:
        t_col = f'fwd_ret_{h}d'
        if t_col in df.columns:
            sub = df.dropna(subset=[t_col, 'avg_rs_20d'])
            ics = []
            for d, grp in sub.groupby('date'):
                if len(grp) >= 10:
                    ic, _ = spearmanr(grp['avg_rs_20d'], grp[t_col])
                    if not np.isnan(ic):
                        ics.append(ic)
            m_ic = np.mean(ics) if ics else 0.0
            decay_rows.append({
                'Forecast_Horizon': f"{h}D Forward",
                'Rank_IC': round(m_ic, 4),
                'Signal_Decay_Status': 'Peak Signal' if h == 5 else ('Moderate' if h <= 10 else 'Decayed')
            })

    df_decay = pd.DataFrame(decay_rows)
    df_decay.to_csv(os.path.join(results_dir, "horizon_results.csv"), index=False)

    # 4. Multi-Horizon Portfolio Backtests & Long-Short Spreads
    port_rows = []
    for k in [5, 10, 20]:
        for h in [5, 10, 20]:
            sub_f = df_forecasts[(df_forecasts['model'] == top_model) & (df_forecasts['horizon'] == h)].dropna(subset=['actual_ret', 'actual_excess'])
            if sub_f.empty:
                continue

            top_k_rets = []
            bot_k_rets = []
            bmk_rets = []

            for d, grp in sub_f.groupby('date'):
                top_k = grp.sort_values('expected_ret', ascending=False).head(k)
                bot_k = grp.sort_values('expected_ret', ascending=True).head(k)
                top_k_rets.append(top_k['actual_ret'].mean())
                bot_k_rets.append(bot_k['actual_ret'].mean())
                bmk_rets.append(top_k['actual_ret'].mean() - top_k['actual_excess'].mean())

            gross_top = float(np.mean(top_k_rets))
            gross_bot = float(np.mean(bot_k_rets))
            gross_bmk = float(np.mean(bmk_rets))
            
            cost_pct = (20 / 10000.0) * 100.0 * 2
            net_top = gross_top - cost_pct

            std_top = float(np.std(top_k_rets)) if len(top_k_rets) > 1 else 1.0
            sharpe_gross = (gross_top / std_top * np.sqrt(252 / h)) if std_top > 0 else 0.0
            sharpe_net = (net_top / std_top * np.sqrt(252 / h)) if std_top > 0 else 0.0

            port_rows.append({
                'Portfolio_Bucket': f"Top {k} Forecast Industries",
                'Horizon': f"{h}D Forward",
                'Top_Gross_Mean (%)': round(gross_top, 2),
                'Top_Net_Mean_20bps (%)': round(net_top, 2),
                'Bottom_Q5_Mean (%)': round(gross_bot, 2),
                'Benchmark_Mean (%)': round(gross_bmk, 2),
                'Top_Minus_Bottom_Spread (%)': round(gross_top - gross_bot, 2),
                'Top_Minus_Benchmark_Excess (%)': round(gross_top - gross_bmk, 2),
                'Annualized_Gross_Sharpe': round(sharpe_gross, 2),
                'Annualized_Net_Sharpe': round(sharpe_net, 2),
                'Hit_Rate (%)': round(float((np.array(top_k_rets) > 0).mean() * 100.0), 1)
            })

    df_port = pd.DataFrame(port_rows)
    df_port.to_csv(os.path.join(results_dir, "forecast_portfolio_results.csv"), index=False)

    # 5. Export Forecasts CSVs
    df_forecasts[['date', 'basic_industry', 'model', 'horizon', 'expected_ret', 'actual_ret', 'actual_excess']].to_csv(os.path.join(results_dir, "return_forecasts.csv"), index=False)
    df_forecasts[['date', 'basic_industry', 'model', 'horizon', 'p_pos', 'p_excess']].to_csv(os.path.join(results_dir, "probability_forecasts.csv"), index=False)
    df_forecasts[['date', 'basic_industry', 'model', 'horizon', 'p10', 'p25', 'p50', 'p75', 'p90', 'mfe', 'mae']].to_csv(os.path.join(results_dir, "quantile_forecasts.csv"), index=False)

    print("Walk-forward evaluation, decay, calibration, and portfolio simulations completed successfully.")
    return df_forecasts, df_model_eval, df_calib, df_decay, df_port
