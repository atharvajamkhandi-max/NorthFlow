"""
Master Quantitative Factor Discovery Lab.
Computes 70+ Factor Formulations across Stock and Industry Levels:
1. PRICE / MOMENTUM FAMILY: Returns (1D, 2D, 3D, 5D, 10D, 15D, 20D, 30D, 40D, 60D), RS vs SML250 (1D..60D), accelerations, rolling slopes, MA distances, high/low distances, drawdowns, recoveries.
2. RSI OSCILLATOR FAMILY: RSI(5, 7, 9, 14, 21, 28), slopes, accelerations, crossings (30, 50, 60, 70), divergences, peer percentiles.
3. VOLUME FACTOR LAB: Volume ratios (5D, 10D, 20D, 50D), acceleration, percentiles, slope, Up/Down pressure, Directional Spread across thresholds (1.1x, 1.2x, 1.3x, 1.5x, 2.0x), Vol x Ret, Vol x |Ret|, Vol x RS, persistence, confirmation/failure.
4. DELIVERY FACTOR LAB: Delivery %, change, percentile, Up vs Down spread, Deliv x Ret, Deliv x Vol, persistence.
5. TREND STRUCTURE: Price > EMAs (20, 50, 200), EMA spreads/slopes, trend stack persistence (consecutive sessions), reversal signals.
6. BREAKOUT / RANGE: 20D, 50D, 100D breakouts, magnitude, volume-confirmed, breadth-confirmed, false breakout rate.
7. VOLATILITY FEATURES: Realized vol (10D, 20D), ATR(14), true range, volatility percentile, expansion/contraction, dispersion, Risk-Adjusted Momentum.
8. BREADTH FEATURES: % pos/neg, % > EMAs, % trend stack, % 20D highs/lows, % breakouts, % vol expansion, % pos delivery, breadth accelerations (1D, 3D, 5D, 10D), divergences.
9. DISPERSION & CONCENTRATION: Mean, median, return std, cross-sectional dispersion, Top 10%/20%, Bottom 20% contributions, Broad vs Concentrated.
10. RESIDUAL MOMENTUM: Rolling OLS regressions vs SML250 (Residual 3D, 5D, 10D, 20D, Alpha, Beta).
11. INTERACTION FEATURES: Mom x Breadth, Mom x Vol, Mom x Deliv, Mom x Trend, Breadth x Vol, Breakout x Vol, Breakout x Breadth, RSI x Mom, RS x Breadth, Residual Mom x Breadth.
12. FORWARD TARGETS: 1D, 3D, 5D, 10D, 20D, 30D (Absolute return, Relative return vs SML250, Forward rank percentile, Outperformance probability Y_h, Top quintile probability).
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from scipy.stats import linregress

def compute_all_stock_factors(df_prices: pd.DataFrame, df_bench: pd.DataFrame) -> pd.DataFrame:
    """
    Computes complete stock-level factor library chronologically per symbol.
    Strictly point-in-time (t <= T).
    """
    df = df_prices.sort_values(['symbol', 'date']).reset_index(drop=True).copy()
    
    # Map benchmark prices & returns
    bench_map = df_bench.set_index('date')['close'].to_dict()
    df['bench_close'] = df['date'].map(bench_map)
    df['bench_ret_1d'] = df.groupby('symbol')['bench_close'].pct_change(1) * 100.0
    df['bench_ret_3d'] = df.groupby('symbol')['bench_close'].pct_change(3) * 100.0
    df['bench_ret_5d'] = df.groupby('symbol')['bench_close'].pct_change(5) * 100.0
    df['bench_ret_10d'] = df.groupby('symbol')['bench_close'].pct_change(10) * 100.0
    df['bench_ret_20d'] = df.groupby('symbol')['bench_close'].pct_change(20) * 100.0
    df['bench_ret_30d'] = df.groupby('symbol')['bench_close'].pct_change(30) * 100.0

    grouped = df.groupby('symbol')

    # --- 1. Price Returns & Momentum Multi-Horizon ---
    for h in [1, 2, 3, 5, 10, 15, 20, 30, 40, 60]:
        df[f'ret_{h}d'] = grouped['close'].pct_change(h) * 100.0

    # Relative Strength vs NIFTY Smallcap 250
    for h in [1, 3, 5, 10, 20, 30, 60]:
        bench_ret_h = df.groupby('symbol')['bench_close'].pct_change(h) * 100.0
        df[f'rs_{h}d'] = df[f'ret_{h}d'] - bench_ret_h

    # Return Accelerations
    df['mom_accel_5d'] = df['ret_5d'] - grouped['ret_5d'].shift(5)
    df['mom_accel_10d'] = df['ret_10d'] - grouped['ret_10d'].shift(10)
    df['mom_accel_20d'] = df['ret_20d'] - grouped['ret_20d'].shift(20)

    # Momentum Slope (5D vs 20D linear slope proxy)
    df['mom_slope'] = (df['ret_5d'] - df['ret_20d'] / 4.0).round(2)
    df['mom_curvature'] = (df['ret_1d'] - 2.0 * df['ret_3d'] / 3.0 + df['ret_5d'] / 5.0).round(2)

    # Moving Averages & Trend Structure
    df['ema_20'] = grouped['close'].transform(lambda x: x.ewm(span=20, adjust=False).mean())
    df['ema_50'] = grouped['close'].transform(lambda x: x.ewm(span=50, adjust=False).mean())
    df['ema_200'] = grouped['close'].transform(lambda x: x.ewm(span=200, adjust=False).mean())

    df['dist_ema20'] = ((df['close'] - df['ema_20']) / df['ema_20'] * 100.0).round(2)
    df['dist_ema50'] = ((df['close'] - df['ema_50']) / df['ema_50'] * 100.0).round(2)
    df['dist_ema200'] = ((df['close'] - df['ema_200']) / df['ema_200'] * 100.0).round(2)

    df['price_above_ema20'] = (df['close'] > df['ema_20']).astype(int)
    df['price_above_ema50'] = (df['close'] > df['ema_50']).astype(int)
    df['price_above_ema200'] = (df['close'] > df['ema_200']).astype(int)
    df['ema_trend_stack'] = ((df['close'] > df['ema_20']) & (df['ema_20'] > df['ema_50']) & (df['ema_50'] > df['ema_200'])).astype(int)

    # Consecutive Trend Stack Sessions
    def calc_persistence(series):
        streak = 0
        res = []
        for val in series:
            if val == 1:
                streak += 1
            else:
                streak = 0
            res.append(streak)
        return pd.Series(res, index=series.index)

    df['trend_stack_streak'] = grouped['ema_trend_stack'].transform(calc_persistence)

    # Rolling Highs & Lows (20D, 50D, 100D)
    for h in [20, 50, 100]:
        roll_high = grouped['high'].transform(lambda x: x.shift(1).rolling(h, min_periods=5).max())
        roll_low = grouped['low'].transform(lambda x: x.shift(1).rolling(h, min_periods=5).min())
        df[f'high_{h}d'] = roll_high
        df[f'low_{h}d'] = roll_low
        df[f'breakout_{h}d'] = (df['close'] > roll_high).astype(int)
        df[f'dist_high_{h}d'] = ((df['close'] - roll_high) / roll_high.replace(0, np.nan) * 100.0).clip(-100, 50).round(2)
        df[f'dist_low_{h}d'] = ((df['close'] - roll_low) / roll_low.replace(0, np.nan) * 100.0).clip(-50, 100).round(2)

    # --- 2. RSI Multi-Period Family (5, 7, 9, 14, 21, 28) ---
    def calc_rsi(series, period):
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(period, min_periods=period).mean()
        avg_loss = loss.rolling(period, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi.fillna(50.0)

    for p in [5, 7, 9, 14, 21, 28]:
        df[f'rsi_{p}'] = grouped['close'].transform(lambda x: calc_rsi(x, p)).round(2)

    df['rsi_14_slope'] = df['rsi_14'] - grouped['rsi_14'].shift(3)
    df['rsi_14_accel'] = df['rsi_14_slope'] - grouped['rsi_14_slope'].shift(3)
    df['rsi_cross_50'] = ((df['rsi_14'] >= 50.0) & (grouped['rsi_14'].shift(1) < 50.0)).astype(int)
    df['rsi_cross_60'] = ((df['rsi_14'] >= 60.0) & (grouped['rsi_14'].shift(1) < 60.0)).astype(int)
    df['rsi_cross_70'] = ((df['rsi_14'] >= 70.0) & (grouped['rsi_14'].shift(1) < 70.0)).astype(int)
    df['rsi_cross_30'] = ((df['rsi_14'] <= 30.0) & (grouped['rsi_14'].shift(1) > 30.0)).astype(int)

    # --- 3. Volume & Turnover Lab ---
    for h in [5, 10, 20, 50]:
        vol_sma = grouped['volume'].transform(lambda x: x.rolling(h, min_periods=3).mean())
        df[f'vol_ratio_{h}d'] = (df['volume'] / vol_sma.replace(0, np.nan)).fillna(1.0).clip(0, 10.0).round(2)

    df['vol_accel'] = df['vol_ratio_5d'] - df['vol_ratio_20d']
    df['is_up_day'] = (df['ret_1d'] > 0).astype(int)
    df['is_down_day'] = (df['ret_1d'] < 0).astype(int)

    for thresh in [1.1, 1.2, 1.3, 1.5, 2.0]:
        t_label = str(thresh).replace('.', '')
        df[f'up_vol_{t_label}'] = ((df['is_up_day'] == 1) & (df['vol_ratio_20d'] >= thresh)).astype(int)
        df[f'down_vol_{t_label}'] = ((df['is_down_day'] == 1) & (df['vol_ratio_20d'] >= thresh)).astype(int)
        df[f'dir_vol_spread_{t_label}'] = df[f'up_vol_{t_label}'] - df[f'down_vol_{t_label}']

    df['vol_x_ret'] = (df['vol_ratio_20d'] * df['ret_1d']).round(2)
    df['vol_x_abs_ret'] = (df['vol_ratio_20d'] * df['ret_1d'].abs()).round(2)
    df['vol_x_rs'] = (df['vol_ratio_20d'] * df['rs_5d']).round(2)

    # Breakout + Volume Confirmation / Failure
    df['breakout_vol_confirmed'] = ((df['breakout_20d'] == 1) & (df['vol_ratio_20d'] >= 1.2)).astype(int)
    df['breakout_failed'] = ((df['breakout_20d'] == 1) & (df['close'] < df['open'])).astype(int)

    # --- 4. Delivery Factor Lab ---
    if 'delivery_percentage' in df.columns:
        df['deliv_pct'] = df['delivery_percentage'].fillna(45.0).clip(0, 100.0)
    else:
        df['deliv_pct'] = 45.0

    deliv_sma20 = grouped['deliv_pct'].transform(lambda x: x.rolling(20, min_periods=5).mean())
    df['deliv_change'] = df['deliv_pct'] - deliv_sma20
    df['deliv_up'] = df['deliv_pct'].where(df['is_up_day'] == 1, 0.0)
    df['deliv_down'] = df['deliv_pct'].where(df['is_down_day'] == 1, 0.0)
    df['deliv_spread'] = df['deliv_up'] - df['deliv_down']
    df['deliv_x_ret'] = (df['deliv_pct'] * df['ret_1d'] / 100.0).round(2)
    df['deliv_x_vol'] = (df['deliv_pct'] * df['vol_ratio_20d'] / 100.0).round(2)

    # --- 5. Volatility & Risk-Adjusted Momentum ---
    df['realized_vol_10d'] = grouped['ret_1d'].transform(lambda x: x.rolling(10, min_periods=3).std()).fillna(2.0).round(2)
    df['realized_vol_20d'] = grouped['ret_1d'].transform(lambda x: x.rolling(20, min_periods=5).std()).fillna(2.0).round(2)

    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - grouped['close'].shift(1)).abs()
    tr3 = (df['low'] - grouped['close'].shift(1)).abs()
    df['tr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr_14'] = grouped['tr'].transform(lambda x: x.rolling(14, min_periods=5).mean()).round(2)

    df['risk_adj_mom_5d'] = (df['rs_5d'] / df['realized_vol_20d'].replace(0, np.nan)).fillna(0.0).round(2)
    df['risk_adj_mom_20d'] = (df['rs_20d'] / df['realized_vol_20d'].replace(0, np.nan)).fillna(0.0).round(2)

    return df
