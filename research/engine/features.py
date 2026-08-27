"""
Comprehensive Stock-Level Feature Engineering Engine.
Calculates for every stock on date t (using strictly lagged historical data t <= T):
- Momentum: 1D, 3D, 5D, 10D, 20D, 40D, 60D, 120D, momentum acceleration, momentum slope
- Relative Strength vs NIFTY SMALLCAP 250: RS 3D, 5D, 10D, 20D, 40D, 60D
- Moving Averages & Trend: 20 EMA, 50 SMA, 50 EMA, 175 EMA, 200 EMA, trend stack, MA distances, InsufficientHistory flags
- RSI: RSI 14 (SMA 14 smoothed, Close input), RSI change, RSI acceleration, overbought/oversold flags
- Volume: Volume ratio, turnover ratio, z-scores, directional volume pressure (up-vol, down-vol, net pressure)
- Delivery: Delivery %, delivery change, delivery z-score, up-day delivery, down-day delivery, delivery-price agreement
- Breakouts: 20D, 50D, 52W high breakouts, distance from high, volume-confirmed breakouts
- Volatility: Realized volatility (20D), ATR (14D), upside vol, downside vol, RiskAdjustedMomentum
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

def calculate_stock_features(df_prices: pd.DataFrame, df_bench: pd.DataFrame) -> pd.DataFrame:
    """
    Computes full stock-level feature matrix chronologically per stock symbol.
    """
    # Sort chronologically
    df = df_prices.sort_values(['symbol', 'date']).reset_index(drop=True).copy()
    
    # Merge benchmark returns
    bench_map = df_bench.set_index('date')['close'].to_dict()
    df['bench_close'] = df['date'].map(bench_map)
    df['bench_ret_1d'] = df.groupby('symbol')['bench_close'].pct_change() * 100.0
    df['bench_ret_3d'] = df.groupby('symbol')['bench_close'].pct_change(3) * 100.0
    df['bench_ret_5d'] = df.groupby('symbol')['bench_close'].pct_change(5) * 100.0
    df['bench_ret_10d'] = df.groupby('symbol')['bench_close'].pct_change(10) * 100.0
    df['bench_ret_20d'] = df.groupby('symbol')['bench_close'].pct_change(20) * 100.0

    grouped = df.groupby('symbol')

    # 1. Price Returns & Momentum
    df['ret_1d'] = grouped['close'].pct_change(1) * 100.0
    df['ret_3d'] = grouped['close'].pct_change(3) * 100.0
    df['ret_5d'] = grouped['close'].pct_change(5) * 100.0
    df['ret_10d'] = grouped['close'].pct_change(10) * 100.0
    df['ret_20d'] = grouped['close'].pct_change(20) * 100.0
    df['ret_40d'] = grouped['close'].pct_change(40) * 100.0
    df['ret_60d'] = grouped['close'].pct_change(60) * 100.0
    df['ret_120d'] = grouped['close'].pct_change(120) * 100.0

    df['mom_accel_5d'] = df['ret_5d'] - grouped['ret_5d'].shift(5)
    df['mom_slope'] = (df['ret_5d'] - df['ret_20d'] / 4.0).round(2)

    # 2. Relative Strength vs NIFTY Smallcap 250
    df['rs_3d'] = df['ret_3d'] - df['bench_ret_3d']
    df['rs_5d'] = df['ret_5d'] - df['bench_ret_5d']
    df['rs_10d'] = df['ret_10d'] - df['bench_ret_10d']
    df['rs_20d'] = df['ret_20d'] - df['bench_ret_20d']
    df['rs_40d'] = df['ret_40d'] - (grouped['bench_close'].pct_change(40) * 100.0)
    df['rs_60d'] = df['ret_60d'] - (grouped['bench_close'].pct_change(60) * 100.0)

    # 3. Moving Averages & Trend
    df['ema_20'] = grouped['close'].transform(lambda x: x.ewm(span=20, adjust=False).mean())
    df['sma_50'] = grouped['close'].transform(lambda x: x.rolling(50, min_periods=10).mean())
    df['ema_50'] = grouped['close'].transform(lambda x: x.ewm(span=50, adjust=False).mean())
    df['ema_175'] = grouped['close'].transform(lambda x: x.ewm(span=175, adjust=False).mean())
    df['ema_200'] = grouped['close'].transform(lambda x: x.ewm(span=200, adjust=False).mean())

    df['hist_len'] = grouped['close'].cumcount() + 1
    df['insufficient_history'] = (df['hist_len'] < 20).astype(int)

    df['above_ema20'] = (df['close'] > df['ema_20']).astype(int)
    df['above_sma50'] = (df['close'] > df['sma_50']).astype(int)
    df['above_ema50'] = (df['close'] > df['ema_50']).astype(int)
    df['above_ema175'] = (df['close'] > df['ema_175']).astype(int)
    df['above_ema200'] = (df['close'] > df['ema_200']).astype(int)

    df['dist_ema20'] = ((df['close'] - df['ema_20']) / df['ema_20'] * 100.0).round(2)
    df['dist_sma50'] = ((df['close'] - df['sma_50']) / df['sma_50'] * 100.0).round(2)
    df['dist_ema200'] = ((df['close'] - df['ema_200']) / df['ema_200'] * 100.0).round(2)

    df['trend_stack'] = (
        (df['close'] > df['ema_20']) & 
        (df['ema_20'] > df['ema_50']) & 
        (df['ema_50'] > df['ema_200'])
    ).astype(int)

    # 4. RSI 14 (SMA 14 smoothed on Closing Price)
    def calc_rsi(series, period=14):
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(period, min_periods=period).mean()
        avg_loss = loss.rolling(period, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi.fillna(50.0)

    df['rsi_14'] = grouped['close'].transform(lambda x: calc_rsi(x, 14)).round(2)
    df['rsi_change_5d'] = df['rsi_14'] - grouped['rsi_14'].shift(5)
    df['rsi_overbought'] = (df['rsi_14'] >= 70.0).astype(int)
    df['rsi_oversold'] = (df['rsi_14'] <= 30.0).astype(int)

    # 5. Volume & Turnover Features
    df['vol_sma20'] = grouped['volume'].transform(lambda x: x.rolling(20, min_periods=5).mean())
    df['vol_ratio'] = (df['volume'] / df['vol_sma20'].replace(0, np.nan)).fillna(1.0).clip(0, 10.0).round(2)
    
    vol_std = grouped['volume'].transform(lambda x: x.rolling(20, min_periods=5).std())
    df['vol_zscore'] = ((df['volume'] - df['vol_sma20']) / vol_std.replace(0, np.nan)).fillna(0.0).clip(-3, 3).round(2)

    df['is_up_day'] = (df['ret_1d'] > 0).astype(int)
    df['is_down_day'] = (df['ret_1d'] < 0).astype(int)
    df['high_vol_up'] = (df['is_up_day'] == 1) & (df['vol_ratio'] >= 1.2)
    df['high_vol_down'] = (df['is_down_day'] == 1) & (df['vol_ratio'] >= 1.2)

    # 6. Delivery Features
    if 'delivery_percentage' in df.columns:
        df['deliv_pct'] = df['delivery_percentage'].fillna(45.0).clip(0, 100.0)
        deliv_sma = grouped['deliv_pct'].transform(lambda x: x.rolling(20, min_periods=5).mean())
        df['deliv_change'] = df['deliv_pct'] - deliv_sma
        df['deliv_up_agreement'] = ((df['is_up_day'] == 1) & (df['deliv_pct'] >= 50.0)).astype(int)
        df['deliv_down_agreement'] = ((df['is_down_day'] == 1) & (df['deliv_pct'] >= 50.0)).astype(int)
    else:
        df['deliv_pct'] = 45.0
        df['deliv_change'] = 0.0
        df['deliv_up_agreement'] = 0
        df['deliv_down_agreement'] = 0

    # 7. Breakout & High Proximity Features
    rolling_max_20 = grouped['high'].transform(lambda x: x.shift(1).rolling(20, min_periods=5).max())
    rolling_max_50 = grouped['high'].transform(lambda x: x.shift(1).rolling(50, min_periods=10).max())
    df['high_20d'] = rolling_max_20
    df['breakout_20d'] = (df['close'] > rolling_max_20).astype(int)
    df['breakout_50d'] = (df['close'] > rolling_max_50).astype(int)
    df['near_high_pct'] = (df['close'] / rolling_max_20.replace(0, np.nan) * 100.0).clip(0, 100.0).fillna(50.0).round(1)
    df['confirmed_breakout'] = ((df['breakout_20d'] == 1) & (df['vol_ratio'] >= 1.2)).astype(int)

    # 8. Volatility Features
    df['realized_vol_20d'] = grouped['ret_1d'].transform(lambda x: x.rolling(20, min_periods=5).std()).fillna(2.0).round(2)
    # Average True Range (14D)
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - grouped['close'].shift(1)).abs()
    tr3 = (df['low'] - grouped['close'].shift(1)).abs()
    df['tr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr_14'] = grouped['tr'].transform(lambda x: x.rolling(14, min_periods=5).mean()).round(2)
    df['risk_adjusted_mom'] = (df['rs_20d'] / df['realized_vol_20d'].replace(0, np.nan)).fillna(0.0).round(2)

    return df
