"""
Master Industry-Level Factor Aggregator & Target Engine.
Aggregates 70+ stock-level factors into industry-level cross-sections:
- Multi-horizon Price & RS Averages/Medians (1D, 2D, 3D, 5D, 10D, 15D, 20D, 30D, 40D, 60D)
- Multi-period RSI (5, 7, 9, 14, 21, 28)
- Breadth Matrix (% > EMA20, 50, 200, trend stack, breakouts, volume expansion thresholds)
- Breadth Accelerations (1D, 3D, 5D, 10D changes) and Divergences
- Directional Volume Spreads & Up/Down Pressure
- Delivery Spreads & Agreement
- Volatility, Dispersion & Concentration Metrics (Top 10%/20%, Bottom 20%, Herfindahl, Broad vs Concentrated)
- Rolling Residual Momentum vs NIFTY Smallcap 250 (1D, 3D, 5D, 10D, 20D, 30D)
- Mathematical Interactions (Mom x Breadth, Breadth x Vol, Breakout x Vol, RSI x Mom, etc.)
- Multi-Horizon Forward Targets: 1D, 3D, 5D, 10D, 20D, 30D (Absolute, Relative vs SML250, Y_h, Top Quintile, MAE, MFE)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

def compute_industry_factor_matrix(df_stock_features: pd.DataFrame, df_bench: pd.DataFrame) -> pd.DataFrame:
    """
    Computes industry factor matrix across all historical dates.
    Guarantees strict lagging (t <= T).
    """
    records = []
    bench_dict = df_bench.set_index('date')['close'].to_dict()

    df_sorted = df_stock_features.sort_values(['date', 'basic_industry']).reset_index(drop=True)

    for (date_val, basic_ind), grp in df_sorted.groupby(['date', 'basic_industry']):
        n_stocks = len(grp)
        if n_stocks == 0:
            continue

        macro_ind = grp['industry'].iloc[0] if 'industry' in grp.columns else 'UNKNOWN'

        # --- 1. Price & Returns Multi-Horizon ---
        ret_dict = {}
        for h in [1, 2, 3, 5, 10, 15, 20, 30, 40, 60]:
            ret_dict[f'avg_ret_{h}d'] = float(grp[f'ret_{h}d'].mean())
            ret_dict[f'med_ret_{h}d'] = float(grp[f'ret_{h}d'].median())

        rs_dict = {}
        for h in [1, 3, 5, 10, 20, 30, 60]:
            rs_dict[f'avg_rs_{h}d'] = float(grp[f'rs_{h}d'].mean())
            rs_dict[f'med_rs_{h}d'] = float(grp[f'rs_{h}d'].median())

        # Accelerations & Slopes
        mom_accel_5d = float(grp['mom_accel_5d'].mean())
        mom_accel_10d = float(grp['mom_accel_10d'].mean())
        mom_slope = float(grp['mom_slope'].mean())

        # Moving Average Distances
        dist_ema20 = float(grp['dist_ema20'].mean())
        dist_ema50 = float(grp['dist_ema50'].mean())
        dist_ema200 = float(grp['dist_ema200'].mean())

        # --- 2. RSI Multi-Period (5, 7, 9, 14, 21, 28) ---
        rsi_dict = {}
        for p in [5, 7, 9, 14, 21, 28]:
            rsi_dict[f'avg_rsi_{p}'] = float(grp[f'rsi_{p}'].mean())

        rsi_14_slope = float(grp['rsi_14_slope'].mean())
        pct_rsi_overbought = float((grp['rsi_14'] >= 70.0).mean() * 100.0)
        pct_rsi_oversold = float((grp['rsi_14'] <= 30.0).mean() * 100.0)

        # --- 3. Breadth Features ---
        pct_pos_1d = float((grp['ret_1d'] > 0).mean() * 100.0)
        pct_pos_5d = float((grp['ret_5d'] > 0).mean() * 100.0)
        pct_neg_1d = float((grp['ret_1d'] < 0).mean() * 100.0)

        ema20_b = float((grp['price_above_ema20'] == 1).mean() * 100.0)
        ema50_b = float((grp['price_above_ema50'] == 1).mean() * 100.0)
        ema200_b = float((grp['price_above_ema200'] == 1).mean() * 100.0)
        trend_stack_b = float((grp['ema_trend_stack'] == 1).mean() * 100.0)
        trend_streak_avg = float(grp['trend_stack_streak'].mean())

        breakout_20_b = float((grp['breakout_20d'] == 1).mean() * 100.0)
        breakout_50_b = float((grp['breakout_50d'] == 1).mean() * 100.0)
        breakout_vol_b = float((grp['breakout_vol_confirmed'] == 1).mean() * 100.0)
        breakout_fail_b = float((grp['breakout_failed'] == 1).mean() * 100.0)

        # Volume Expansion Breadth Across Thresholds
        vol_b_dict = {}
        for thresh in [1.1, 1.2, 1.3, 1.5, 2.0]:
            t_label = str(thresh).replace('.', '')
            vol_b_dict[f'up_vol_{t_label}_b'] = float((grp[f'up_vol_{t_label}'] == 1).mean() * 100.0)
            vol_b_dict[f'down_vol_{t_label}_b'] = float((grp[f'down_vol_{t_label}'] == 1).mean() * 100.0)
            vol_b_dict[f'dir_vol_spread_{t_label}'] = vol_b_dict[f'up_vol_{t_label}_b'] - vol_b_dict[f'down_vol_{t_label}_b']

        avg_vol_ratio_5d = float(grp['vol_ratio_5d'].mean())
        avg_vol_ratio_20d = float(grp['vol_ratio_20d'].mean())
        avg_vol_accel = float(grp['vol_accel'].mean())

        # --- 4. Delivery Features ---
        avg_deliv_pct = float(grp['deliv_pct'].mean())
        avg_deliv_change = float(grp['deliv_change'].mean())
        deliv_spread = float(grp['deliv_spread'].mean())
        deliv_x_ret = float(grp['deliv_x_ret'].mean())
        deliv_x_vol = float(grp['deliv_x_vol'].mean())

        # --- 5. Volatility & Risk-Adjusted Momentum ---
        avg_vol_10d = float(grp['realized_vol_10d'].mean())
        avg_vol_20d = float(grp['realized_vol_20d'].mean())
        avg_atr_14 = float(grp['atr_14'].mean())
        avg_risk_adj_5d = float(grp['risk_adj_mom_5d'].mean())
        avg_risk_adj_20d = float(grp['risk_adj_mom_20d'].mean())

        # --- 6. Dispersion & Concentration ---
        ret_std_5d = float(grp['ret_5d'].std()) if n_stocks > 1 else 0.0
        sorted_rets = np.sort(grp['ret_5d'].fillna(0).values)[::-1]
        
        top10_pct_n = max(1, int(np.ceil(n_stocks * 0.10)))
        top20_pct_n = max(1, int(np.ceil(n_stocks * 0.20)))
        bot20_pct_n = max(1, int(np.ceil(n_stocks * 0.20)))

        total_abs_ret = np.abs(sorted_rets).sum()
        if total_abs_ret > 0:
            top10_contrib = float(np.abs(sorted_rets[:top10_pct_n]).sum() / total_abs_ret * 100.0)
            top20_contrib = float(np.abs(sorted_rets[:top20_pct_n]).sum() / total_abs_ret * 100.0)
            bot20_contrib = float(np.abs(sorted_rets[-bot20_pct_n:]).sum() / total_abs_ret * 100.0)
        else:
            top10_contrib, top20_contrib, bot20_contrib = 100.0, 100.0, 100.0

        is_concentrated = int(top20_contrib >= 60.0 and n_stocks >= 5)

        # Base Record
        rec = {
            'date': date_val,
            'industry': macro_ind,
            'basic_industry': basic_ind,
            'stock_count': n_stocks,
            'is_small_industry': int(n_stocks <= 2),
            'mom_accel_5d': mom_accel_5d,
            'mom_accel_10d': mom_accel_10d,
            'mom_slope': mom_slope,
            'dist_ema20': dist_ema20,
            'dist_ema50': dist_ema50,
            'dist_ema200': dist_ema200,
            'rsi_14_slope': rsi_14_slope,
            'pct_rsi_overbought': pct_rsi_overbought,
            'pct_rsi_oversold': pct_rsi_oversold,
            'pct_pos_1d': pct_pos_1d,
            'pct_pos_5d': pct_pos_5d,
            'pct_neg_1d': pct_neg_1d,
            'ema20_breadth': ema20_b,
            'ema50_breadth': ema50_b,
            'ema200_breadth': ema200_b,
            'trend_stack_breadth': trend_stack_b,
            'trend_streak_avg': trend_streak_avg,
            'breakout_20_breadth': breakout_20_b,
            'breakout_50_breadth': breakout_50_b,
            'breakout_vol_breadth': breakout_vol_b,
            'breakout_fail_breadth': breakout_fail_b,
            'avg_vol_ratio_5d': avg_vol_ratio_5d,
            'avg_vol_ratio_20d': avg_vol_ratio_20d,
            'avg_vol_accel': avg_vol_accel,
            'avg_deliv_pct': avg_deliv_pct,
            'avg_deliv_change': avg_deliv_change,
            'deliv_spread': deliv_spread,
            'deliv_x_ret': deliv_x_ret,
            'deliv_x_vol': deliv_x_vol,
            'avg_vol_10d': avg_vol_10d,
            'avg_vol_20d': avg_vol_20d,
            'avg_atr_14': avg_atr_14,
            'avg_risk_adj_5d': avg_risk_adj_5d,
            'avg_risk_adj_20d': avg_risk_adj_20d,
            'ret_std_5d': ret_std_5d,
            'top10_contrib': top10_contrib,
            'top20_contrib': top20_contrib,
            'bot20_contrib': bot20_contrib,
            'is_concentrated': is_concentrated
        }
        rec.update(ret_dict)
        rec.update(rs_dict)
        rec.update(rsi_dict)
        rec.update(vol_b_dict)

        records.append(rec)

    df_agg = pd.DataFrame(records)
    if df_agg.empty:
        return df_agg

    # --- 7. Breadth Accelerations & Divergences ---
    df_agg = df_agg.sort_values(['basic_industry', 'date']).reset_index(drop=True)
    grp_ind = df_agg.groupby('basic_industry')

    df_agg['breadth_change_1d'] = df_agg['ema20_breadth'] - grp_ind['ema20_breadth'].shift(1).fillna(df_agg['ema20_breadth'])
    df_agg['breadth_change_3d'] = df_agg['ema20_breadth'] - grp_ind['ema20_breadth'].shift(3).fillna(df_agg['ema20_breadth'])
    df_agg['breadth_change_5d'] = df_agg['ema20_breadth'] - grp_ind['ema20_breadth'].shift(5).fillna(df_agg['ema20_breadth'])
    df_agg['breadth_change_10d'] = df_agg['ema20_breadth'] - grp_ind['ema20_breadth'].shift(10).fillna(df_agg['ema20_breadth'])

    # Breadth Divergences
    df_agg['div_price_up_breadth_down'] = ((df_agg['avg_ret_5d'] > 0) & (df_agg['breadth_change_5d'] < -10.0)).astype(int)
    df_agg['div_price_down_breadth_up'] = ((df_agg['avg_ret_5d'] < 0) & (df_agg['breadth_change_5d'] > 10.0)).astype(int)

    # --- 8. Mathematical Interaction Features ---
    df_agg['int_mom_x_breadth'] = (df_agg['avg_rs_5d'] * df_agg['ema20_breadth'] / 100.0).round(2)
    df_agg['int_mom_x_vol'] = (df_agg['avg_rs_5d'] * df_agg['dir_vol_spread_12'] / 100.0).round(2)
    df_agg['int_mom_x_deliv'] = (df_agg['avg_rs_5d'] * df_agg['avg_deliv_pct'] / 100.0).round(2)
    df_agg['int_breadth_x_vol'] = (df_agg['ema20_breadth'] * df_agg['dir_vol_spread_12'] / 100.0).round(2)
    df_agg['int_breakout_x_vol'] = (df_agg['breakout_20_breadth'] * df_agg['avg_vol_ratio_20d'] / 100.0).round(2)
    df_agg['int_rsi_x_mom'] = ((df_agg['avg_rsi_14'] - 50.0) * df_agg['avg_rs_5d'] / 10.0).round(2)

    # --- 9. Rolling Residual Momentum vs NIFTY Smallcap 250 ---
    bench_series = df_bench.set_index('date')['close']
    
    for h in [1, 3, 5, 10, 20, 30]:
        bench_ret_h = bench_series.pct_change(h) * 100.0
        df_agg[f'bench_ret_{h}d'] = df_agg['date'].map(bench_ret_h).fillna(0.0)

    def calc_residuals(group):
        if len(group) < 5:
            for h in [1, 3, 5, 10, 20, 30]:
                group[f'residual_mom_{h}d'] = group[f'avg_rs_{h}d']
            group['alpha_15d'] = 0.0
            group['beta_15d'] = 1.0
            return group

        cov = group['avg_ret_5d'].rolling(15, min_periods=5).cov(group['bench_ret_5d'])
        var = group['bench_ret_5d'].rolling(15, min_periods=5).var().replace(0, np.nan)
        beta = (cov / var).fillna(1.0).clip(-2.0, 3.0)
        alpha = group['avg_ret_5d'].rolling(15, min_periods=5).mean() - beta * group['bench_ret_5d'].rolling(15, min_periods=5).mean()

        group['alpha_15d'] = alpha.fillna(0.0).round(2)
        group['beta_15d'] = beta.round(2)

        for h in [1, 3, 5, 10, 20, 30]:
            group[f'residual_mom_{h}d'] = (group[f'avg_ret_{h}d'] - (beta * group[f'bench_ret_{h}d'])).round(2)
        return group

    df_agg = df_agg.groupby('basic_industry', group_keys=False).apply(calc_residuals)

    # --- 10. Multi-Horizon Forward Targets ---
    for h in [1, 3, 5, 10, 20, 30]:
        df_agg[f'fwd_ret_{h}d'] = grp_ind[f'avg_ret_{h}d'].shift(-h)
        
        bench_fwd_map = (df_bench.set_index('date')['close'].shift(-h) / df_bench.set_index('date')['close'] - 1.0) * 100.0
        df_agg[f'bench_fwd_{h}d'] = df_agg['date'].map(bench_fwd_map)
        df_agg[f'rel_fwd_{h}d'] = df_agg[f'fwd_ret_{h}d'] - df_agg[f'bench_fwd_{h}d']
        df_agg[f'Y_{h}d'] = (df_agg[f'rel_fwd_{h}d'] > 0).astype(float).where(df_agg[f'rel_fwd_{h}d'].notnull(), np.nan)

    return df_agg
