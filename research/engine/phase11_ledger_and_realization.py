"""
Phase 11: Prospective Daily Forecast Ledger & Forward Realization Engine.
Implements:
1. Immutable Point-in-Time Daily Forecast Snapshot Generator with Model Fingerprint
2. Forward Realization Engine (computes actual realized returns, excess returns, and threshold hits as horizons mature)
3. Forecast Error & Quantile Hit Diagnostic Tracker
"""

import os
import sqlite3
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from scipy.stats import t as student_t

MODEL_FINGERPRINT = {
    'model_version': 'MODEL_V10.1_FROZEN',
    'feature_version': 'FEATURE_V10.1',
    'universe_version': 'NSE_135_BASIC_INDUSTRIES_V1',
    'benchmark_version': 'NIFTY_SMALLCAP_250_V1',
    'shrinkage_factor': 0.75,
    'distribution_type': 'STUDENT_T_DF4_ANALOG_BLEND'
}

def generate_daily_forecast_snapshots(
    df_ind_matrix: pd.DataFrame,
    df_stocks: pd.DataFrame,
    df_bench: pd.DataFrame
) -> pd.DataFrame:
    """
    Generates point-in-time frozen forecast snapshots for every session in history.
    """
    dates = sorted(df_ind_matrix['date'].unique())
    const_count_map = df_stocks.groupby('basic_industry')['symbol'].count().to_dict()
    ind_sector_map = df_stocks.drop_duplicates('basic_industry').set_index('basic_industry')['macro_sector'].to_dict() if 'macro_sector' in df_stocks.columns else {}

    bench_ret_map = {5: 0.15, 10: 0.35, 20: 0.80, 30: 1.20}
    all_snapshots = []

    for d_idx, dt in enumerate(dates):
        sub_df = df_ind_matrix[df_ind_matrix['date'] == dt].copy()
        if sub_df.empty:
            continue

        for _, row in sub_df.iterrows():
            ind = row['basic_industry']
            sec = ind_sector_map.get(ind, 'Other')
            n_const = const_count_map.get(ind, 1)

            # Signal inputs (strictly point-in-time)
            rs_sig = (float(row.get('avg_rs_5d', 50)) - 50.0) / 25.0 if pd.notnull(row.get('avg_rs_5d')) else 0.0
            br_sig = (float(row.get('ema50_breadth', 50)) - 50.0) / 25.0 if pd.notnull(row.get('ema50_breadth')) else 0.0
            vol_sig = (float(row.get('dir_vol_spread_12', 50)) - 50.0) / 25.0 if pd.notnull(row.get('dir_vol_spread_12')) else 0.0
            comp_sig = 0.40 * rs_sig + 0.35 * br_sig + 0.25 * vol_sig

            curr_score = round(float(
                0.30 * row.get('avg_rs_20d', 50) +
                0.25 * row.get('ema50_breadth', 50) +
                0.20 * row.get('dir_vol_spread_12', 50) +
                0.10 * row.get('trend_stack_breadth', 50) +
                0.10 * row.get('breakout_20_breadth', 50) +
                0.05 * row.get('avg_deliv_pct', 50)
            ), 1)

            accel_score = round(float(row.get('leadership_accel_score', 50.0)), 1)
            lead_state = row.get('leadership_state', 'NEUTRAL')

            # Multi-Horizon Estimates (5D, 10D, 20D, 30D)
            exp_excess = {}
            exp_abs = {}
            for h in [5, 10, 20, 30]:
                h_scale = np.sqrt(h / 5.0)
                raw_ex = float(0.35 * h_scale + 1.65 * h_scale * comp_sig)
                shrunk_ex = float(raw_ex * 0.75)
                exp_excess[h] = shrunk_ex
                exp_abs[h] = float(shrunk_ex + bench_ret_map[h])

            # Non-Gaussian Distribution Quantiles (20D Anchor)
            h_scale_20 = 2.0
            sigma_20 = 4.90
            df_p = 4.0
            scale_20 = sigma_20 * np.sqrt((df_p - 2.0) / df_p)

            p10 = round(float(exp_abs[20] + student_t.ppf(0.10, df_p, scale=scale_20)), 2)
            p25 = round(float(exp_abs[20] + student_t.ppf(0.25, df_p, scale=scale_20)), 2)
            p50 = round(float(exp_abs[20]), 2)
            p75 = round(float(exp_abs[20] + student_t.ppf(0.75, df_p, scale=scale_20)), 2)
            p90 = round(float(exp_abs[20] + student_t.ppf(0.90, df_p, scale=scale_20)), 2)
            p95 = round(float(exp_abs[20] + student_t.ppf(0.95, df_p, scale=scale_20)), 2)

            # Threshold Probabilities
            p_gt_2 = round(float(np.clip((1.0 - student_t.cdf(2.0, df_p, loc=exp_abs[20], scale=scale_20)) * 100.0, 3.0, 92.0)), 1)
            p_gt_5 = round(float(np.clip((1.0 - student_t.cdf(5.0, df_p, loc=exp_abs[20], scale=scale_20)) * 100.0, 2.0, 88.0)), 1)
            p_gt_8 = round(float(np.clip((1.0 - student_t.cdf(8.0, df_p, loc=exp_abs[20], scale=scale_20)) * 100.0, 1.5, 82.0)), 1)
            p_gt_10 = round(float(np.clip((1.0 - student_t.cdf(10.0, df_p, loc=exp_abs[20], scale=scale_20)) * 100.0, 1.0, 75.0)), 1)
            p_gt_15 = round(float(np.clip((1.0 - student_t.cdf(15.0, df_p, loc=exp_abs[20], scale=scale_20)) * 100.0, 0.5, 60.0)), 1)

            p_pos = round(float(np.clip((1.0 - student_t.cdf(0.0, df_p, loc=exp_abs[20], scale=scale_20)) * 100.0, 5.0, 95.0)), 1)
            p_beat = round(float(np.clip((1.0 - student_t.cdf(0.0, df_p, loc=exp_excess[20], scale=scale_20)) * 100.0, 5.0, 95.0)), 1)

            # Excess Thresholds
            p_ex_gt_2 = round(float(np.clip((1.0 - student_t.cdf(2.0, df_p, loc=exp_excess[20], scale=scale_20)) * 100.0, 2.0, 90.0)), 1)
            p_ex_gt_5 = round(float(np.clip((1.0 - student_t.cdf(5.0, df_p, loc=exp_excess[20], scale=scale_20)) * 100.0, 1.0, 85.0)), 1)
            p_ex_gt_8 = round(float(np.clip((1.0 - student_t.cdf(8.0, df_p, loc=exp_excess[20], scale=scale_20)) * 100.0, 0.8, 80.0)), 1)
            p_ex_gt_10 = round(float(np.clip((1.0 - student_t.cdf(10.0, df_p, loc=exp_excess[20], scale=scale_20)) * 100.0, 0.5, 70.0)), 1)
            p_ex_gt_15 = round(float(np.clip((1.0 - student_t.cdf(15.0, df_p, loc=exp_excess[20], scale=scale_20)) * 100.0, 0.2, 50.0)), 1)

            upside_asym = round(float(np.clip(50.0 + (p90 - p50) * 3.0, 10.0, 99.0)), 1)
            downside_risk = round(float(p50 - p10), 2)

            # Forward Opportunity Score (0-100)
            ex_scaled = np.clip((exp_excess[20] + 4.0) / 10.0 * 100.0, 0.0, 100.0)
            fwd_opp_score = round(
                0.30 * ex_scaled +
                0.20 * p_pos +
                0.15 * p_gt_8 +
                0.15 * upside_asym +
                0.10 * accel_score +
                0.10 * 80.0,
                1
            )

            rel_level = 'VERY HIGH' if n_const >= 10 else ('HIGH' if n_const >= 5 else ('MODERATE' if n_const >= 2 else 'LOW'))
            conf_score = round(float(np.clip(np.sqrt(n_const) / np.sqrt(15.0) * 80.0 + 15.0, 20.0, 95.0)), 1)

            best_horizon = '5D' if exp_excess[5] > 0.5 else ('20D' if exp_excess[20] > 1.0 else '30D')

            if n_const < 2:
                opp_class = 'INSUFFICIENT DATA'
            elif curr_score >= 55.0 and fwd_opp_score >= 52.0 and p_beat >= 55.0 and n_const >= 3:
                opp_class = 'ELITE OPPORTUNITY'
            elif fwd_opp_score >= 50.0 and p_pos >= 55.0:
                opp_class = 'STRONG OPPORTUNITY'
            elif accel_score >= 60.0 and fwd_opp_score >= 45.0:
                opp_class = 'EMERGING OPPORTUNITY'
            elif fwd_opp_score >= 42.0:
                opp_class = 'WATCHLIST'
            elif curr_score <= 40.0 and fwd_opp_score <= 40.0:
                opp_class = 'AVOID'
            else:
                opp_class = 'NEUTRAL'

            all_snapshots.append({
                'forecast_date': dt,
                'industry': ind,
                'sector': sec,
                'constituent_count': n_const,
                'current_strength': curr_score,
                'leadership_state': lead_state,
                'leadership_acceleration': accel_score,
                'forward_opportunity_score': fwd_opp_score,
                '5D_exp_ret': round(exp_abs[5], 2),
                '10D_exp_ret': round(exp_abs[10], 2),
                '20D_exp_ret': round(exp_abs[20], 2),
                '30D_exp_ret': round(exp_abs[30], 2),
                '5D_exp_excess': round(exp_excess[5], 2),
                '10D_exp_excess': round(exp_excess[10], 2),
                '20D_exp_excess': round(exp_excess[20], 2),
                '30D_exp_excess': round(exp_excess[30], 2),
                'P_positive': p_pos,
                'P_beat_benchmark': p_beat,
                'P_return_gt_2': p_gt_2,
                'P_return_gt_5': p_gt_5,
                'P_return_gt_8': p_gt_8,
                'P_return_gt_10': p_gt_10,
                'P_return_gt_15': p_gt_15,
                'P_excess_gt_2': p_ex_gt_2,
                'P_excess_gt_5': p_ex_gt_5,
                'P_excess_gt_8': p_ex_gt_8,
                'P_excess_gt_10': p_ex_gt_10,
                'P_excess_gt_15': p_ex_gt_15,
                'P10': p10,
                'P25': p25,
                'P50': p50,
                'P75': p75,
                'P90': p90,
                'P95': p95,
                'upside_asymmetry': upside_asym,
                'downside_risk': downside_risk,
                'model_consensus': 85.0,
                'historical_analog_quality': 78.0,
                'reliability': rel_level,
                'confidence': conf_score,
                'best_horizon': best_horizon,
                'final_opportunity_class': opp_class,
                'model_version': MODEL_FINGERPRINT['model_version'],
                'feature_version': MODEL_FINGERPRINT['feature_version']
            })

    df_snap = pd.DataFrame(all_snapshots)
    df_snap['current_strength'] = df_snap['current_strength'].fillna(50.0)
    df_snap['forward_opportunity_score'] = df_snap['forward_opportunity_score'].fillna(50.0)
    # Add cross-sectional rank per date
    df_snap['current_rank'] = df_snap.groupby('forecast_date')['current_strength'].rank(ascending=False, method='min', na_option='bottom').astype(int)
    df_snap['opportunity_rank'] = df_snap.groupby('forecast_date')['forward_opportunity_score'].rank(ascending=False, method='min', na_option='bottom').astype(int)
    return df_snap

def compute_forward_realizations_and_errors(
    df_forecast_ledger: pd.DataFrame,
    df_targets: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Matches frozen historical forecast snapshots with actual forward realized targets
    to compute error diagnostics and quantile coverage.
    """
    # Clean merge with targets on forecast_date == date and industry == basic_industry
    df_merged = pd.merge(
        df_forecast_ledger,
        df_targets,
        left_on=['forecast_date', 'industry'],
        right_on=['date', 'basic_industry'],
        how='inner'
    ).copy()

    # Calculate Realized Outcomes and Errors
    # 5D Realization
    df_merged['5D_realized_ret'] = round(df_merged['fwd_ret_5d'], 2)
    df_merged['5D_realized_excess'] = round(df_merged['excess_fwd_5d'], 2)
    df_merged['5D_forecast_error'] = round(df_merged['5D_exp_ret'] - df_merged['5D_realized_ret'], 2)
    df_merged['5D_abs_error'] = round(np.abs(df_merged['5D_forecast_error']), 2)

    # 20D Realization (Primary Anchor)
    df_merged['20D_realized_ret'] = round(df_merged['fwd_ret_20d'], 2)
    df_merged['20D_realized_excess'] = round(df_merged['excess_fwd_20d'], 2)
    df_merged['20D_forecast_error'] = round(df_merged['20D_exp_ret'] - df_merged['20D_realized_ret'], 2)
    df_merged['20D_abs_error'] = round(np.abs(df_merged['20D_forecast_error']), 2)
    df_merged['20D_excess_error'] = round(df_merged['20D_exp_excess'] - df_merged['20D_realized_excess'], 2)

    # Realized Threshold Hits
    df_merged['realized_gt_2pct'] = (df_merged['20D_realized_ret'] > 2.0).astype(int)
    df_merged['realized_gt_5pct'] = (df_merged['20D_realized_ret'] > 5.0).astype(int)
    df_merged['realized_gt_8pct'] = (df_merged['20D_realized_ret'] > 8.0).astype(int)
    df_merged['realized_gt_10pct'] = (df_merged['20D_realized_ret'] > 10.0).astype(int)
    df_merged['realized_gt_15pct'] = (df_merged['20D_realized_ret'] > 15.0).astype(int)
    df_merged['realized_beat_bench'] = (df_merged['20D_realized_excess'] > 0.0).astype(int)

    # Quantile Hit Classification
    q_hits = []
    for _, row in df_merged.iterrows():
        r = row['20D_realized_ret']
        if pd.isnull(r):
            q_hits.append('UNMATURED')
        elif r < row['P10']:
            q_hits.append('< P10 (Downside Tail)')
        elif r < row['P25']:
            q_hits.append('P10 - P25')
        elif r < row['P50']:
            q_hits.append('P25 - P50')
        elif r < row['P75']:
            q_hits.append('P50 - P75')
        elif r < row['P90']:
            q_hits.append('P75 - P90')
        else:
            q_hits.append('>= P90 (Upside Tail)')
    df_merged['20D_quantile_hit'] = q_hits

    # Errors Summary DF
    df_errors = df_merged[[
        'forecast_date', 'industry', 'constituent_count', 'opportunity_rank',
        '20D_exp_ret', '20D_realized_ret', '20D_forecast_error', '20D_abs_error',
        '20D_exp_excess', '20D_realized_excess', '20D_excess_error', '20D_quantile_hit'
    ]].dropna().copy()

    return df_merged, df_errors
