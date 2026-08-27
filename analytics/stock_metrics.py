"""
Stock-Level Analytics Engine.
Calculates returns, exponential moving averages (20, 50, 200), volume & turnover ratios,
high proximity, moving average trend stack alignment, relative strength vs benchmark (NIFTY SMALLCAP 250),
and 20-session breakout flags.
Strictly eliminates look-ahead bias by lagging historical reference windows.
"""

import logging
from typing import Optional, List
import pandas as pd
import numpy as np

from database.db import Database

logger = logging.getLogger(__name__)


class StockMetricsCalculator:
    """
    Computes rolling and cross-sectional technical metrics for all stocks in the database.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    def calculate_all_stock_metrics(self, target_date: Optional[str] = None) -> int:
        """
        Calculates and updates stock metrics in the database.
        If target_date is specified, persists metrics only for target_date.
        Otherwise persists metrics for all valid historical dates.
        """
        logger.info(f"Loading price history for stock metrics calculation (target_date={target_date})...")
        
        # Load all daily prices
        df_prices = self.db.get_daily_prices()
        if df_prices.empty:
            logger.warning("No price data found in daily_prices.")
            return 0

        # Load benchmark prices
        df_bench = self.db.get_benchmark_prices()
        bench_returns = {}
        if not df_bench.empty:
            df_bench = df_bench.sort_values('date').reset_index(drop=True)
            df_bench['bench_ret_5d'] = df_bench['close'].pct_change(5) * 100.0
            df_bench['bench_ret_20d'] = df_bench['close'].pct_change(20) * 100.0
            for _, r in df_bench.iterrows():
                bench_returns[r['date']] = {
                    'ret_5d': r['bench_ret_5d'],
                    'ret_20d': r['bench_ret_20d']
                }

        # Process per-stock time series
        df_prices = df_prices.sort_values(['symbol', 'date']).reset_index(drop=True)
        
        metrics_list = []
        for symbol, group in df_prices.groupby('symbol'):
            group = group.copy().sort_values('date').reset_index(drop=True)
            
            # 1. Returns
            group['return_1d'] = group['close'].pct_change(1) * 100.0
            if pd.isna(group.loc[0, 'return_1d']) and pd.notnull(group.loc[0, 'previous_close']) and group.loc[0, 'previous_close'] > 0:
                group.loc[0, 'return_1d'] = ((group.loc[0, 'close'] - group.loc[0, 'previous_close']) / group.loc[0, 'previous_close']) * 100.0

            group['return_5d'] = group['close'].pct_change(5) * 100.0
            group['return_20d'] = group['close'].pct_change(20) * 100.0

            # 2. Moving Averages (EMA)
            group['ema20'] = group['close'].ewm(span=20, adjust=False).mean()
            group['ema50'] = group['close'].ewm(span=50, adjust=False).mean()
            group['ema200'] = group['close'].ewm(span=200, adjust=False).mean()

            group['above_20ema'] = (group['close'] > group['ema20']).astype(int)
            group['above_50ema'] = (group['close'] > group['ema50']).astype(int)
            group['above_200ema'] = (group['close'] > group['ema200']).astype(int)

            group['dist_ema20'] = ((group['close'] - group['ema20']) / group['ema20']) * 100.0
            group['dist_ema50'] = ((group['close'] - group['ema50']) / group['ema50']) * 100.0

            # 3. Moving Average Trend Stack Alignment (100: Full Bullish Stack, 65: Above 20 EMA, 40: Above 50 EMA, 15: Below)
            c = group['close']
            e20 = group['ema20']
            e50 = group['ema50']
            conds_ts = [
                (e50.notnull()) & (c >= e20) & (e20 >= e50),
                (c >= e20),
                (e50.notnull()) & (c >= e50)
            ]
            choices_ts = [100.0, 65.0, 40.0]
            group['trend_stack'] = np.select(conds_ts, choices_ts, default=15.0)

            # 4. Volume metrics: previous 20-session avg volume strictly excluding today
            group['avg_volume_20d'] = group['volume'].shift(1).rolling(20, min_periods=5).mean()
            group['volume_ratio'] = np.where(
                (group['avg_volume_20d'].notnull()) & (group['avg_volume_20d'] > 0),
                group['volume'] / group['avg_volume_20d'],
                1.0
            )

            # 5. Turnover metrics (Rupee Capital Flow)
            if 'turnover' not in group.columns or group['turnover'].isnull().all():
                group['turnover'] = group['volume'] * group['close']

            group['avg_turnover_20d'] = group['turnover'].shift(1).rolling(20, min_periods=5).mean()
            group['turnover_ratio'] = np.where(
                (group['avg_turnover_20d'].notnull()) & (group['avg_turnover_20d'] > 0),
                group['turnover'] / group['avg_turnover_20d'],
                1.0
            )

            # Turnover quality: reward turnover expansion when 5D return >= 0, penalize on distribution
            tr = group['turnover_ratio'].fillna(1.0)
            r5 = group['return_5d']
            conds_t = [
                (r5.notnull()) & (r5 < 0.0)
            ]
            choices_t = [
                1.0 / np.maximum(1.0, tr)
            ]
            group['turnover_quality'] = np.select(conds_t, choices_t, default=np.minimum(4.0, tr))

            # 6. Proximity to Highs (Lookback peak including current day)
            rolling_high_20d = group['high'].rolling(20, min_periods=1).max()
            group['high_proximity'] = (group['close'] / rolling_high_20d).clip(0.5, 1.0) * 100.0

            # 7. Breakout: 20-session previous high strictly excluding today
            group['prev_20_high'] = group['high'].shift(1).rolling(20, min_periods=5).max()
            group['is_breakout_20d'] = np.where(
                (group['prev_20_high'].notnull()) & (group['close'] > group['prev_20_high']),
                1,
                0
            )

            # 8. Relative Strength vs Benchmark
            rs_5d_list = []
            rs_20d_list = []
            for _, row in group.iterrows():
                dt = row['date']
                b_info = bench_returns.get(dt, {})
                b_5d = b_info.get('ret_5d', np.nan)
                b_20d = b_info.get('ret_20d', np.nan)

                rs_5 = (row['return_5d'] - b_5d) if (pd.notnull(row['return_5d']) and pd.notnull(b_5d)) else row['return_5d']
                rs_20 = (row['return_20d'] - b_20d) if (pd.notnull(row['return_20d']) and pd.notnull(b_20d)) else row['return_20d']
                rs_5d_list.append(rs_5)
                rs_20d_list.append(rs_20)

            group['rs_5d'] = rs_5d_list
            group['rs_20d'] = rs_20d_list
            group['leadership_score'] = 0.0  # Computed in scoring module

            metrics_list.append(group)

        df_metrics_all = pd.concat(metrics_list, ignore_index=True)

        cols_to_save = [
            'date', 'symbol', 'close', 'return_1d', 'return_5d', 'return_20d',
            'ema20', 'ema50', 'ema200', 'volume', 'avg_volume_20d', 'volume_ratio',
            'turnover', 'avg_turnover_20d', 'turnover_ratio', 'turnover_quality',
            'high_proximity', 'trend_stack',
            'rs_5d', 'rs_20d', 'is_breakout_20d', 'above_20ema', 'above_50ema',
            'above_200ema', 'dist_ema20', 'dist_ema50', 'leadership_score'
        ]

        if target_date:
            df_to_save = df_metrics_all[df_metrics_all['date'] == target_date][cols_to_save]
        else:
            df_to_save = df_metrics_all[cols_to_save]

        inserted = self.db.insert_or_replace_df("stock_metrics", df_to_save)
        logger.info(f"Saved {inserted} stock metrics records into stock_metrics table.")
        return inserted
