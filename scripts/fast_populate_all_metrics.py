"""
Vectorized Fast Metrics Population across all 403 sessions.
"""

import os
import sys
import time
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.db import Database

def run_fast_metrics():
    print("=" * 80)
    print(" VECTORIZED FAST METRICS POPULATION ACROSS 403 SESSIONS")
    print("=" * 80)
    t0 = time.time()
    db = Database()

    # 1. Load Prices & Benchmark
    with db.get_connection() as conn:
        df_prices = pd.read_sql_query("SELECT dp.*, s.industry, s.basic_industry FROM daily_prices dp LEFT JOIN stocks s ON dp.symbol = s.symbol ORDER BY dp.symbol ASC, dp.date ASC;", conn)
        df_bench = pd.read_sql_query("SELECT * FROM market_benchmark ORDER BY date ASC;", conn)

    print(f"Loaded {len(df_prices):,} price rows across {df_prices['date'].nunique()} dates in {time.time() - t0:.1f}s")

    # 2. Vectorized Stock Metrics
    print("Computing vectorized stock metrics...")
    grp = df_prices.groupby('symbol')
    
    df_prices['return_1d'] = grp['close'].pct_change(1) * 100.0
    df_prices['return_5d'] = grp['close'].pct_change(5) * 100.0
    df_prices['return_20d'] = grp['close'].pct_change(20) * 100.0

    df_prices['ema20'] = grp['close'].transform(lambda x: x.ewm(span=20, adjust=False).mean())
    df_prices['ema50'] = grp['close'].transform(lambda x: x.ewm(span=50, adjust=False).mean())
    df_prices['ema200'] = grp['close'].transform(lambda x: x.ewm(span=200, adjust=False).mean())

    df_prices['above_20ema'] = (df_prices['close'] > df_prices['ema20']).astype(int)
    df_prices['above_50ema'] = (df_prices['close'] > df_prices['ema50']).astype(int)
    df_prices['above_200ema'] = (df_prices['close'] > df_prices['ema200']).astype(int)

    df_prices['dist_ema20'] = ((df_prices['close'] - df_prices['ema20']) / df_prices['ema20'] * 100.0).round(2)
    df_prices['dist_ema50'] = ((df_prices['close'] - df_prices['ema50']) / df_prices['ema50'] * 100.0).round(2)

    # Trend stack
    c = df_prices['close']
    e20 = df_prices['ema20']
    e50 = df_prices['ema50']
    conds = [(e50.notnull()) & (c >= e20) & (e20 >= e50), (c >= e20), (e50.notnull()) & (c >= e50)]
    df_prices['trend_stack'] = np.select(conds, [100.0, 65.0, 40.0], default=15.0)

    # Volume & Turnover
    df_prices['avg_volume_20d'] = grp['volume'].transform(lambda x: x.shift(1).rolling(20, min_periods=5).mean())
    df_prices['volume_ratio'] = np.where((df_prices['avg_volume_20d'].notnull()) & (df_prices['avg_volume_20d'] > 0), df_prices['volume'] / df_prices['avg_volume_20d'], 1.0)

    if 'turnover' not in df_prices.columns or df_prices['turnover'].isnull().all():
        df_prices['turnover'] = df_prices['volume'] * df_prices['close']
    df_prices['avg_turnover_20d'] = grp['turnover'].transform(lambda x: x.shift(1).rolling(20, min_periods=5).mean())
    df_prices['turnover_ratio'] = np.where((df_prices['avg_turnover_20d'].notnull()) & (df_prices['avg_turnover_20d'] > 0), df_prices['turnover'] / df_prices['avg_turnover_20d'], 1.0)

    tr = df_prices['turnover_ratio'].fillna(1.0)
    r5 = df_prices['return_5d']
    df_prices['turnover_quality'] = np.select([(r5.notnull()) & (r5 < 0.0)], [1.0 / np.maximum(1.0, tr)], default=np.minimum(4.0, tr))

    rolling_high_20d = grp['high'].transform(lambda x: x.rolling(20, min_periods=1).max())
    df_prices['high_proximity'] = (df_prices['close'] / rolling_high_20d).clip(0.5, 1.0) * 100.0

    prev_20_high = grp['high'].transform(lambda x: x.shift(1).rolling(20, min_periods=5).max())
    df_prices['is_breakout_20d'] = np.where((prev_20_high.notnull()) & (df_prices['close'] > prev_20_high), 1, 0)

    # Relative Strength vs Smallcap 250
    bench_5d = df_bench.set_index('date')['return_5d'].to_dict() if 'return_5d' in df_bench.columns else {}
    bench_20d = df_bench.set_index('date')['return_20d'].to_dict() if 'return_20d' in df_bench.columns else {}
    df_prices['bench_ret_5d'] = df_prices['date'].map(bench_5d)
    df_prices['bench_ret_20d'] = df_prices['date'].map(bench_20d)
    df_prices['rs_5d'] = df_prices['return_5d'] - df_prices['bench_ret_5d']
    df_prices['rs_20d'] = df_prices['return_20d'] - df_prices['bench_ret_20d']

    df_prices['leadership_score'] = (
        0.30 * df_prices['rs_20d'].clip(-30, 30) * 1.66 + 50.0 * 0.30 +
        0.30 * df_prices['trend_stack'] +
        0.20 * df_prices['volume_ratio'].clip(0, 4) * 25.0 +
        0.20 * df_prices['high_proximity']
    ).clip(0, 100).round(2)

    stk_cols = [
        'date', 'symbol', 'close', 'return_1d', 'return_5d', 'return_20d',
        'ema20', 'ema50', 'ema200', 'volume', 'avg_volume_20d', 'volume_ratio',
        'turnover', 'avg_turnover_20d', 'turnover_ratio', 'turnover_quality',
        'high_proximity', 'trend_stack', 'rs_5d', 'rs_20d', 'is_breakout_20d',
        'above_20ema', 'above_50ema', 'above_200ema', 'dist_ema20', 'dist_ema50', 'leadership_score'
    ]
    df_stk_insert = df_prices[[c for c in stk_cols if c in df_prices.columns]].copy()
    
    print(f"Inserting {len(df_stk_insert):,} stock_metrics rows into SQLite...")
    db.insert_or_replace_df("stock_metrics", df_stk_insert)

    # 3. Vectorized Industry Metrics across 135 Basic Industries
    print("Computing vectorized industry metrics across all 135 Basic Industries...")
    valid_ind = df_prices[df_prices['basic_industry'].notnull() & (df_prices['basic_industry'] != 'UNKNOWN')].copy()
    
    ind_grp = valid_ind.groupby(['date', 'basic_industry', 'industry'])
    df_ind = ind_grp.agg(
        stock_count=('symbol', 'count'),
        avg_return_1d=('return_1d', 'mean'),
        median_return_1d=('return_1d', 'median'),
        avg_return_5d=('return_5d', 'mean'),
        median_return_5d=('return_5d', 'median'),
        avg_return_20d=('return_20d', 'mean'),
        median_return_20d=('return_20d', 'median'),
        industry_rs_5d=('rs_5d', 'mean'),
        industry_rs_20d=('rs_20d', 'mean'),
        avg_volume_ratio=('volume_ratio', 'mean'),
        positive_breadth=('return_1d', lambda x: (x > 0).mean() * 100.0),
        ema20_breadth=('above_20ema', lambda x: x.mean() * 100.0),
        ema50_breadth=('above_50ema', lambda x: x.mean() * 100.0),
        ema200_breadth=('above_200ema', lambda x: x.mean() * 100.0),
        breakout_count=('is_breakout_20d', 'sum'),
        breakout_percentage=('is_breakout_20d', lambda x: x.mean() * 100.0),
        avg_delivery_percentage=('delivery_percentage', 'mean')
    ).reset_index()

    df_ind['is_low_sample'] = (df_ind['stock_count'] < 5).astype(int)

    # Derived Money Flow Score (0-100)
    df_ind['score_today'] = (
        0.25 * df_ind['ema20_breadth'] +
        0.25 * df_ind['ema50_breadth'] +
        0.20 * df_ind['industry_rs_20d'].clip(-20, 20) * 2.5 + 50.0 * 0.20 +
        0.15 * df_ind['breakout_percentage'] +
        0.15 * df_ind['avg_volume_ratio'].clip(0, 4) * 25.0
    ).clip(0, 100).round(2)

    df_ind['score_1d_ago'] = df_ind.groupby('basic_industry')['score_today'].shift(1).fillna(df_ind['score_today'])
    df_ind['score_3d_ago'] = df_ind.groupby('basic_industry')['score_today'].shift(3).fillna(df_ind['score_today'])
    df_ind['score_5d_ago'] = df_ind.groupby('basic_industry')['score_today'].shift(5).fillna(df_ind['score_today'])
    
    df_ind['score_change_1d'] = (df_ind['score_today'] - df_ind['score_1d_ago']).round(2)
    df_ind['score_change_3d'] = (df_ind['score_today'] - df_ind['score_3d_ago']).round(2)
    df_ind['score_change_5d'] = (df_ind['score_today'] - df_ind['score_5d_ago']).round(2)

    # Status classification
    conds_status = [
        (df_ind['score_today'] >= 65) & (df_ind['score_change_5d'] >= 3),
        (df_ind['score_today'] >= 60),
        (df_ind['score_today'] < 40) & (df_ind['score_change_5d'] <= -3),
        (df_ind['score_today'] < 40),
        (df_ind['score_change_5d'] >= 5)
    ]
    choices_status = ['Leading - Accelerating', 'Leading', 'Lagging - Deteriorating', 'Lagging', 'Emerging']
    df_ind['status'] = np.select(conds_status, choices_status, default='Consolidating')

    print(f"Inserting {len(df_ind):,} industry_metrics rows into SQLite...")
    db.insert_or_replace_df("industry_metrics", df_ind)

    print("\n" + "=" * 80)
    print(f" FAST POPULATION COMPLETED SUCCESSFULLY IN {time.time() - t0:.1f}s")
    print(f" Total Stock Metrics Rows:     {len(df_stk_insert):,}")
    print(f" Total Industry Metrics Rows:  {len(df_ind):,} across {df_ind['date'].nunique()} dates")
    print("=" * 80)

if __name__ == "__main__":
    run_fast_metrics()
