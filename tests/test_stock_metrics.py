"""
Unit tests for Stock Metrics calculation.
Tests returns, EMA, volume ratio, relative strength, and verifies ZERO look-ahead bias on breakouts.
"""

import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from database.db import Database
from analytics.stock_metrics import StockMetricsCalculator


@pytest.fixture
def metrics_env(tmp_path):
    db_path = tmp_path / "test_stock_metrics.db"
    db = Database(db_path=db_path)
    db.initialize_schema()
    
    # Populate stocks master
    db.insert_or_replace_df("stocks", pd.DataFrame([{
        'symbol': 'POLYCAB',
        'company_name': 'Polycab India Limited',
        'isin': 'INE455K01017',
        'series': 'EQ',
        'industry': 'Capital Goods',
        'basic_industry': 'Wires & Cables',
        'active': 1,
        'last_updated': '2024-08-01 00:00:00'
    }]))
    
    # Create 25 days of synthetic price data for POLYCAB
    dates = [f"2024-08-{i:02d}" for i in range(1, 26)]
    
    prices = []
    for i, dt in enumerate(dates, 1):
        c = 100.0 + i
        h = c + 1.0
        l = c - 1.0
        o = c - 0.5
        v = 10000.0 if i < 25 else 30000.0  # 3x volume surge on day 25
        prices.append({
            'date': dt,
            'symbol': 'POLYCAB',
            'series': 'EQ',
            'open': o,
            'high': h,
            'low': l,
            'close': c,
            'previous_close': c - 1.0,
            'volume': v,
            'turnover': v * c,
            'delivery_quantity': v * 0.5,
            'delivery_percentage': 50.0
        })
    
    db.insert_or_replace_df("daily_prices", pd.DataFrame(prices))
        
    # Benchmark prices
    bench = []
    for dt in dates:
        bench.append({
            'date': dt,
            'index_name': 'NIFTY SMALLCAP 250',
            'open': 24000.0,
            'high': 24050.0,
            'low': 23950.0,
            'close': 24000.0
        })
    db.insert_or_replace_df("market_benchmark", pd.DataFrame(bench))
    
    calc = StockMetricsCalculator(db=db)
    yield calc, db



def test_stock_metrics_look_ahead_bias_and_calculations(metrics_env):
    calc, db = metrics_env
    count = calc.calculate_all_stock_metrics()
    assert count == 25
    
    df_metrics = db.get_latest_stock_metrics(trade_date="2024-08-25")
    assert len(df_metrics) == 1
    row = df_metrics.iloc[0]
    
    # 1. Day 25 close is 125, Day 25 volume is 30000
    assert row['close'] == 125.0
    assert row['volume'] == 30000.0
    
    # 2. Avg volume over previous 20 sessions (days 5 to 24) should be 10000.0
    assert row['avg_volume_20d'] == 10000.0
    # Volume ratio should be 30000 / 10000 = 3.0
    assert pytest.approx(row['volume_ratio'], 0.01) == 3.0
    
    # 3. Returns & Moving averages
    assert row['above_20ema'] == 1
    assert row['dist_ema20'] > 0
    assert row['return_1d'] > 0
    assert row['rs_5d'] > 0
    assert row['company_name'] == 'Polycab India Limited'
    assert row['basic_industry'] == 'Wires & Cables'
