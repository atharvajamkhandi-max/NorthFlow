"""
Industry-Level Aggregation, Breadth, Residual Momentum & Dynamic Constituent Weighting Engine.
Features:
- Breadth Engine (EMA20, 50 SMA, 175 EMA, 200 EMA, trend stack, breakout breadth, high-vol advancing breadth, 3D/5D/10D changes)
- Residual Momentum Engine (Rolling alpha, beta, residual return vs NIFTY Smallcap 250)
- Dynamic Constituent Weighting Engine:
  * Equal Weighting
  * Leadership-Weighted
  * Relative-Strength Weighted
  * Turnover/Liquidity Weighted
  * Risk-Adjusted Momentum Weighted
  * 15% Single-Stock Cap Constraint
  * Concentration metrics (Herfindahl Index, N_eff, Top 1/3/5 contributions)
  * Bottom-Up Aggregated Signals
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

def compute_industry_aggregations(df_stock_features: pd.DataFrame, df_bench: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates stock features into industry cross-sections chronologically.
    Guarantees strict lagging (t <= T).
    """
    records = []
    bench_dict = df_bench.set_index('date')['close'].to_dict()

    # Pre-sort
    df_sorted = df_stock_features.sort_values(['date', 'basic_industry']).reset_index(drop=True)

    for (date_val, basic_ind), grp in df_sorted.groupby(['date', 'basic_industry']):
        n_stocks = len(grp)
        if n_stocks == 0:
            continue

        macro_ind = grp['industry'].iloc[0] if 'industry' in grp.columns else 'UNKNOWN'

        # --- 1. Static & Momentum Breadth ---
        pct_pos_1d = float((grp['ret_1d'] > 0).mean() * 100.0)
        pct_pos_5d = float((grp['ret_5d'] > 0).mean() * 100.0)
        pct_pos_20d = float((grp['ret_20d'] > 0).mean() * 100.0)

        ema20_b = float((grp['above_ema20'] == 1).mean() * 100.0)
        sma50_b = float((grp['above_sma50'] == 1).mean() * 100.0)
        ema50_b = float((grp['above_ema50'] == 1).mean() * 100.0)
        ema175_b = float((grp['above_ema175'] == 1).mean() * 100.0)
        ema200_b = float((grp['above_ema200'] == 1).mean() * 100.0)
        trend_stack_b = float((grp['trend_stack'] == 1).mean() * 100.0)

        breakout_b = float((grp['breakout_20d'] == 1).mean() * 100.0)
        conf_breakout_b = float((grp['confirmed_breakout'] == 1).mean() * 100.0)
        high_vol_up_b = float((grp['high_vol_up'] == 1).mean() * 100.0)
        high_vol_down_b = float((grp['high_vol_down'] == 1).mean() * 100.0)
        net_vol_pressure = high_vol_up_b - high_vol_down_b

        # --- 2. Equal-Weight Averages ---
        avg_ret_1d = float(grp['ret_1d'].mean())
        avg_ret_3d = float(grp['ret_3d'].mean())
        avg_ret_5d = float(grp['ret_5d'].mean())
        avg_ret_10d = float(grp['ret_10d'].mean())
        avg_ret_20d = float(grp['ret_20d'].mean())

        avg_rs_3d = float(grp['rs_3d'].mean())
        avg_rs_5d = float(grp['rs_5d'].mean())
        avg_rs_10d = float(grp['rs_10d'].mean())
        avg_rs_20d = float(grp['rs_20d'].mean())

        avg_rsi_14 = float(grp['rsi_14'].mean())
        avg_vol_ratio = float(grp['vol_ratio'].mean())
        med_vol_ratio = float(grp['vol_ratio'].median())
        avg_deliv_pct = float(grp['deliv_pct'].mean())
        avg_risk_adj_mom = float(grp['risk_adjusted_mom'].mean())

        # --- 3. Dynamic Constituent Weighting Engine ---
        # Candidate Weight A: Equal Weight (1/N)
        w_eq = np.ones(n_stocks) / n_stocks

        # Candidate Weight B: Leadership Weight (clipped positive)
        ls_vals = grp['dist_ema20'].fillna(0).clip(lower=0) + grp['rs_20d'].fillna(0).clip(lower=0) + 1.0
        w_lead = ls_vals.values / ls_vals.sum()

        # Candidate Weight C: Turnover / Liquidity Weight
        to_vals = grp['turnover'].fillna(1000.0).clip(lower=100.0)
        w_turnover = to_vals.values / to_vals.sum()

        # Apply 15% Cap Constraint to weights
        def apply_weight_cap(w, cap=0.15):
            if len(w) <= int(1.0 / cap):
                return np.ones(len(w)) / len(w)
            w_capped = np.clip(w, 0, cap)
            for _ in range(5):
                excess = 1.0 - w_capped.sum()
                uncapped_mask = (w_capped < cap)
                if not uncapped_mask.any() or abs(excess) < 1e-4:
                    break
                w_capped[uncapped_mask] += excess / uncapped_mask.sum()
                w_capped = np.clip(w_capped, 0, cap)
            return w_capped / w_capped.sum()

        w_lead_capped = apply_weight_cap(w_lead, cap=0.15)
        w_to_capped = apply_weight_cap(w_turnover, cap=0.15)

        # Concentration Metrics
        hhi = float((w_lead_capped ** 2).sum())
        n_eff = float(1.0 / max(1e-5, hhi))
        sorted_w = np.sort(w_lead_capped)[::-1]
        top1_contrib = float(sorted_w[0] * 100.0) if len(sorted_w) >= 1 else 100.0
        top3_contrib = float(sorted_w[:3].sum() * 100.0) if len(sorted_w) >= 3 else 100.0
        top5_contrib = float(sorted_w[:5].sum() * 100.0) if len(sorted_w) >= 5 else 100.0

        # Bottom-Up Dynamic Signals
        bu_ret_5d = float((grp['ret_5d'].values * w_lead_capped).sum())
        bu_rs_20d = float((grp['rs_20d'].values * w_lead_capped).sum())
        bu_vol_ratio = float((grp['vol_ratio'].values * w_to_capped).sum())
        bu_rsi = float((grp['rsi_14'].values * w_lead_capped).sum())

        records.append({
            'date': date_val,
            'industry': macro_ind,
            'basic_industry': basic_ind,
            'stock_count': n_stocks,
            'effective_constituents': round(n_eff, 1),
            'herfindahl_index': round(hhi, 3),
            'top1_contrib_pct': round(top1_contrib, 1),
            'top3_contrib_pct': round(top3_contrib, 1),
            'top5_contrib_pct': round(top5_contrib, 1),
            'pct_pos_1d': pct_pos_1d,
            'pct_pos_5d': pct_pos_5d,
            'pct_pos_20d': pct_pos_20d,
            'ema20_breadth': ema20_b,
            'sma50_breadth': sma50_b,
            'ema50_breadth': ema50_b,
            'ema175_breadth': ema175_b,
            'ema200_breadth': ema200_b,
            'trend_stack_breadth': trend_stack_b,
            'breakout_breadth': breakout_b,
            'confirmed_breakout_breadth': conf_breakout_b,
            'high_vol_up_breadth': high_vol_up_b,
            'high_vol_down_breadth': high_vol_down_b,
            'net_vol_pressure': net_vol_pressure,
            'avg_ret_1d': avg_ret_1d,
            'avg_ret_3d': avg_ret_3d,
            'avg_ret_5d': avg_ret_5d,
            'avg_ret_10d': avg_ret_10d,
            'avg_ret_20d': avg_ret_20d,
            'avg_rs_3d': avg_rs_3d,
            'avg_rs_5d': avg_rs_5d,
            'avg_rs_10d': avg_rs_10d,
            'avg_rs_20d': avg_rs_20d,
            'avg_rsi_14': avg_rsi_14,
            'avg_vol_ratio': avg_vol_ratio,
            'med_vol_ratio': med_vol_ratio,
            'avg_deliv_pct': avg_deliv_pct,
            'avg_risk_adj_mom': avg_risk_adj_mom,
            'bu_ret_5d': bu_ret_5d,
            'bu_rs_20d': bu_rs_20d,
            'bu_vol_ratio': bu_vol_ratio,
            'bu_rsi': bu_rsi
        })

    df_agg = pd.DataFrame(records)
    if df_agg.empty:
        return df_agg

    # --- 4. Breadth Changes (3D, 5D, 10D) & Residual Momentum ---
    df_agg = df_agg.sort_values(['basic_industry', 'date']).reset_index(drop=True)
    grp_ind = df_agg.groupby('basic_industry')

    df_agg['breadth_change_3d'] = df_agg['ema20_breadth'] - grp_ind['ema20_breadth'].shift(3).fillna(df_agg['ema20_breadth'])
    df_agg['breadth_change_5d'] = df_agg['ema20_breadth'] - grp_ind['ema20_breadth'].shift(5).fillna(df_agg['ema20_breadth'])
    df_agg['breadth_change_10d'] = df_agg['ema20_breadth'] - grp_ind['ema20_breadth'].shift(10).fillna(df_agg['ema20_breadth'])

    # Benchmark Returns for Residual Momentum
    bench_series = df_bench.set_index('date')['close']
    bench_rets = bench_series.pct_change(5) * 100.0
    df_agg['bench_ret_5d'] = df_agg['date'].map(bench_rets).fillna(0.0)

    # Rolling 15-day Beta & Residual Momentum
    def calc_residual(group):
        if len(group) < 5:
            group['alpha_15d'] = 0.0
            group['beta_15d'] = 1.0
            group['residual_mom_5d'] = group['avg_rs_5d']
            return group
        cov = group['avg_ret_5d'].rolling(15, min_periods=5).cov(group['bench_ret_5d'])
        var = group['bench_ret_5d'].rolling(15, min_periods=5).var().replace(0, np.nan)
        beta = (cov / var).fillna(1.0).clip(-2.0, 3.0)
        alpha = group['avg_ret_5d'].rolling(15, min_periods=5).mean() - beta * group['bench_ret_5d'].rolling(15, min_periods=5).mean()
        residual = group['avg_ret_5d'] - (beta * group['bench_ret_5d'])
        group['alpha_15d'] = alpha.fillna(0.0).round(2)
        group['beta_15d'] = beta.round(2)
        group['residual_mom_5d'] = residual.fillna(group['avg_rs_5d']).round(2)
        return group

    df_agg = df_agg.groupby('basic_industry', group_keys=False).apply(calc_residual)

    # --- 5. Forward Target Labels (Y5, Y10, Y20, RelativeReturn5, 10, 20) ---
    df_agg['fwd_ret_5d'] = grp_ind['avg_ret_5d'].shift(-5)
    df_agg['fwd_ret_10d'] = grp_ind['avg_ret_5d'].shift(-10)
    df_agg['fwd_ret_20d'] = grp_ind['avg_ret_20d'].shift(-20)

    bench_fwd_5d = bench_series.pct_change(-5).abs() * 0.0 # calculate forward bench return
    bench_fwd_map_5 = (df_bench.set_index('date')['close'].shift(-5) / df_bench.set_index('date')['close'] - 1.0) * 100.0
    bench_fwd_map_10 = (df_bench.set_index('date')['close'].shift(-10) / df_bench.set_index('date')['close'] - 1.0) * 100.0
    bench_fwd_map_20 = (df_bench.set_index('date')['close'].shift(-20) / df_bench.set_index('date')['close'] - 1.0) * 100.0

    df_agg['bench_fwd_5d'] = df_agg['date'].map(bench_fwd_map_5)
    df_agg['bench_fwd_10d'] = df_agg['date'].map(bench_fwd_map_10)
    df_agg['bench_fwd_20d'] = df_agg['date'].map(bench_fwd_map_20)

    df_agg['rel_fwd_5d'] = df_agg['fwd_ret_5d'] - df_agg['bench_fwd_5d']
    df_agg['rel_fwd_10d'] = df_agg['fwd_ret_10d'] - df_agg['bench_fwd_10d']
    df_agg['rel_fwd_20d'] = df_agg['fwd_ret_20d'] - df_agg['bench_fwd_20d']

    df_agg['Y5'] = (df_agg['rel_fwd_5d'] > 0).astype(float).where(df_agg['rel_fwd_5d'].notnull(), np.nan)
    df_agg['Y10'] = (df_agg['rel_fwd_10d'] > 0).astype(float).where(df_agg['rel_fwd_10d'].notnull(), np.nan)
    df_agg['Y20'] = (df_agg['rel_fwd_20d'] > 0).astype(float).where(df_agg['rel_fwd_20d'].notnull(), np.nan)

    return df_agg
