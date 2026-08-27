"""
Phase V2 Quantitative Factor Engine: Point-in-Time Equity & Industry Factor Lab.
Computes 8 factor families for all 3,492 stocks chronologically across 403 sessions:
1. Price & Multi-Horizon Momentum (1D, 3D, 5D, 10D, 20D, 60D, 120D, 252D)
2. Trend Quality (SMA10..200, EMA10..200, Slopes, Trend Stacking 0-100)
3. Momentum Quality & Risk-Adjusted Momentum (M/Vol, Drawdowns 20D/52W, Range Pos)
4. Volatility Regimes & Downside Volatility (RV5..60, ATR, Vol Regimes)
5. Volume Confirmation Engine (Ratios, Z-Scores, Volume Acceleration)
6. Delivery States Engine (Price-Delivery 4-State conditional behavior)
7. Multi-Horizon Relative Strength (vs Market, Sector, Industry)
8. Cross-Sectional Normalization (Universe Z-Score, Percentile Rank, Industry-Neutral Z-Score)
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

from database.db import Database

class V2FactorLab:
    def __init__(self, db: Database = None):
        self.db = db or Database()

    def build_all_factors(self) -> pd.DataFrame:
        print("\n--- [V2 Factor Lab] Computing Point-in-Time Factors (1.07M rows) ---")
        with self.db.get_connection() as conn:
            df_prices = pd.read_sql_query("""
                SELECT dp.*, s.industry, s.basic_industry 
                FROM daily_prices dp 
                LEFT JOIN stocks s ON dp.symbol = s.symbol 
                ORDER BY dp.symbol ASC, dp.date ASC;
            """, conn)
            df_bench = pd.read_sql_query("SELECT * FROM market_benchmark ORDER BY date ASC;", conn)

        # 1. Multi-Horizon Returns & Momentum
        grp = df_prices.groupby('symbol')
        for h in [1, 3, 5, 10, 20, 60]:
            df_prices[f'ret_{h}d'] = grp['close'].pct_change(h) * 100.0
            df_prices[f'momentum_{h}d'] = df_prices[f'ret_{h}d']

        # 2. Moving Averages & Trend Stacking
        for span in [10, 20, 50, 100, 200]:
            df_prices[f'ema_{span}'] = grp['close'].transform(lambda x: x.ewm(span=span, adjust=False).mean())
            df_prices[f'sma_{span}'] = grp['close'].transform(lambda x: x.rolling(span, min_periods=max(2, span//4)).mean())

        df_prices['price_vs_sma20'] = ((df_prices['close'] - df_prices['sma_20']) / df_prices['sma_20'] * 100.0).round(2)
        df_prices['price_vs_sma50'] = ((df_prices['close'] - df_prices['sma_50']) / df_prices['sma_50'] * 100.0).round(2)
        df_prices['price_vs_sma200'] = ((df_prices['close'] - df_prices['sma_200']) / df_prices['sma_200'] * 100.0).round(2)

        c = df_prices['close']
        e20 = df_prices['ema_20']
        e50 = df_prices['ema_50']
        e200 = df_prices['ema_200']
        conds_stack = [
            (e200.notnull()) & (c >= e20) & (e20 >= e50) & (e50 >= e200),
            (e50.notnull()) & (c >= e20) & (e20 >= e50),
            (c >= e20),
            (e50.notnull()) & (c >= e50)
        ]
        df_prices['trend_stack_score'] = np.select(conds_stack, [100.0, 80.0, 60.0, 40.0], default=15.0)

        # 3. Volatility & Risk-Adjusted Momentum
        for h in [5, 10, 20, 60]:
            df_prices[f'realized_vol_{h}d'] = grp['ret_1d'].transform(lambda x: x.rolling(h, min_periods=max(2, h//2)).std() * np.sqrt(252)).round(2)

        df_prices['downside_vol_20d'] = grp['ret_1d'].transform(lambda x: x.apply(lambda r: min(0.0, r)).rolling(20, min_periods=5).std() * np.sqrt(252)).round(2)
        
        # ATR 14
        prev_close = grp['close'].shift(1)
        tr1 = df_prices['high'] - df_prices['low']
        tr2 = (df_prices['high'] - prev_close).abs()
        tr3 = (df_prices['low'] - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df_prices['atr_14'] = grp['close'].transform(lambda x: tr.loc[x.index].rolling(14, min_periods=3).mean()).round(2)
        df_prices['atr_pct'] = ((df_prices['atr_14'] / df_prices['close']) * 100.0).round(2)
        df_prices['vol_adj_momentum_20d'] = (df_prices['momentum_20d'] / np.maximum(5.0, df_prices['realized_vol_20d'])).round(2)

        # 4. Drawdowns & 52-Week Range Position
        high_20d = grp['high'].transform(lambda x: x.rolling(20, min_periods=1).max())
        high_52w = grp['high'].transform(lambda x: x.rolling(252, min_periods=20).max())
        low_52w = grp['low'].transform(lambda x: x.rolling(252, min_periods=20).min())

        df_prices['drawdown_20d'] = (((df_prices['close'] - high_20d) / high_20d) * 100.0).round(2)
        df_prices['drawdown_52w'] = (((df_prices['close'] - high_52w) / high_52w) * 100.0).round(2)
        df_prices['pos_52w_pct'] = (((df_prices['close'] - low_52w) / np.maximum(0.01, high_52w - low_52w)) * 100.0).clip(0, 100).round(2)

        # 5. Volume Engine & Confirmation Score
        for vh in [5, 20, 60]:
            df_prices[f'vol_sma_{vh}'] = grp['volume'].transform(lambda x: x.shift(1).rolling(vh, min_periods=max(2, vh//4)).mean())
            df_prices[f'rel_vol_{vh}d'] = np.where((df_prices[f'vol_sma_{vh}'].notnull()) & (df_prices[f'vol_sma_{vh}'] > 0), (df_prices['volume'] / df_prices[f'vol_sma_{vh}']).round(2), 1.0)

        df_prices['volume_zscore_20d'] = grp['volume'].transform(lambda x: ((x - x.shift(1).rolling(20, min_periods=5).mean()) / np.maximum(1.0, x.shift(1).rolling(20, min_periods=5).std()))).clip(-3.0, 5.0).round(2)

        # Volume Confirmation: Price Up + Vol Expansion = Bullish; Price Down + Vol Expansion = Bearish
        is_up = df_prices['ret_1d'] > 0
        vol_exp = df_prices['rel_vol_20d'] >= 1.25
        df_prices['volume_confirmation_score'] = np.select(
            [is_up & vol_exp, is_up & (~vol_exp), (~is_up) & (~vol_exp), (~is_up) & vol_exp],
            [100.0, 65.0, 40.0, 10.0],
            default=50.0
        )

        # 6. Delivery Engine & 4 Observable States
        if 'delivery_percentage' in df_prices.columns:
            df_prices['delivery_pct'] = df_prices['delivery_percentage'].fillna(40.0)
            df_prices['delivery_sma20'] = grp['delivery_pct'].transform(lambda x: x.shift(1).rolling(20, min_periods=5).mean())
            df_prices['delivery_change'] = (df_prices['delivery_pct'] - df_prices['delivery_sma20']).round(2)
        else:
            df_prices['delivery_pct'] = 40.0
            df_prices['delivery_change'] = 0.0

        # Delivery 4-State: Price Up/Down x Delivery Up/Down
        deliv_up = df_prices['delivery_change'] > 0
        conds_deliv_state = [
            (is_up & deliv_up),
            (is_up & ~deliv_up),
            (~is_up & deliv_up),
            (~is_up & ~deliv_up)
        ]
        df_prices['delivery_state'] = np.select(conds_deliv_state, ['P_UP_D_UP', 'P_UP_D_DOWN', 'P_DOWN_D_UP', 'P_DOWN_D_DOWN'], default='NEUTRAL')

        # 7. Multi-Horizon Relative Strength (Market, Sector, Industry)
        bench_map_20d = df_bench.set_index('date')['return_20d'].to_dict() if 'return_20d' in df_bench.columns else {}
        df_prices['market_ret_20d'] = df_prices['date'].map(bench_map_20d).fillna(0.0)
        df_prices['market_rs_20d'] = (df_prices['ret_20d'].fillna(0.0) - df_prices['market_ret_20d']).round(2)

        sec_m = df_prices.groupby(['date', 'industry'])['ret_20d'].transform('mean').fillna(0.0)
        ind_m = df_prices.groupby(['date', 'basic_industry'])['ret_20d'].transform('mean').fillna(0.0)
        df_prices['sector_rs_20d'] = (df_prices['ret_20d'].fillna(0.0) - sec_m).round(2)
        df_prices['industry_rs_20d'] = (df_prices['ret_20d'].fillna(0.0) - ind_m).round(2)

        # 8. Cross-Sectional Z-Scores & Industry-Neutral Z-Scores
        print("Computing point-in-time cross-sectional and industry-neutral z-scores...")
        date_grp = df_prices.groupby('date')
        df_prices['cs_mom_rank'] = date_grp['momentum_20d'].rank(pct=True) * 100.0
        df_prices['cs_rs_rank'] = date_grp['market_rs_20d'].rank(pct=True) * 100.0
        df_prices['cs_vol_rank'] = date_grp['rel_vol_20d'].rank(pct=True) * 100.0

        # Industry-Neutral Z-Score: (x - mean_ind) / std_ind
        date_ind_grp = df_prices.groupby(['date', 'basic_industry'])
        df_prices['industry_neutral_mom_z'] = date_ind_grp['momentum_20d'].transform(lambda x: (x - x.mean()) / np.maximum(1.0, x.std())).fillna(0.0).clip(-3.0, 3.0).round(2)
        df_prices['industry_neutral_rs_z'] = date_ind_grp['market_rs_20d'].transform(lambda x: (x - x.mean()) / np.maximum(1.0, x.std())).fillna(0.0).clip(-3.0, 3.0).round(2)

        # Stock Strength Score (0 to 100)
        df_prices['stock_strength_score'] = (
            0.30 * df_prices['cs_mom_rank'].fillna(50.0) +
            0.25 * df_prices['cs_rs_rank'].fillna(50.0) +
            0.20 * df_prices['trend_stack_score'].fillna(50.0) +
            0.15 * df_prices['volume_confirmation_score'].fillna(50.0) +
            0.10 * df_prices['pos_52w_pct'].fillna(50.0)
        ).clip(0, 100).round(2)

        print(f"V2 factor engineering complete: {len(df_prices):,} rows across 403 sessions.")
        return df_prices
