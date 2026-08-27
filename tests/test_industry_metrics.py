"""
Unit tests for Industry Metrics Aggregation.
Tests aggregation logic, breadth computations, breakout %, volume ratios, and low sample flags.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from database.db import Database
from analytics.industry_metrics import IndustryMetricsCalculator


@pytest.fixture
def ind_metrics_env(tmp_path):
    db_path = tmp_path / "test_ind_metrics.db"
    db = Database(db_path=db_path)
    db.initialize_schema()
    
    # Setup 4 stocks across 2 industries
    stocks = [
        {'symbol': 'POLYCAB', 'company_name': 'Polycab', 'series': 'EQ', 'industry': 'Capital Goods', 'basic_industry': 'Wires & Cables', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'KEI', 'company_name': 'KEI', 'series': 'EQ', 'industry': 'Capital Goods', 'basic_industry': 'Wires & Cables', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'RRKABEL', 'company_name': 'RR Kabel', 'series': 'EQ', 'industry': 'Capital Goods', 'basic_industry': 'Wires & Cables', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'TRENT', 'company_name': 'Trent', 'series': 'EQ', 'industry': 'Consumer Services', 'basic_industry': 'Retail', 'active': 1, 'last_updated': '2024-08-01'}
    ]
    db.insert_or_replace_df("stocks", pd.DataFrame(stocks))
    
    # Stock metrics for 2024-08-14
    sm = [
        # POLYCAB: +2% 1D, +5% 5D, +10% 20D, above 20 & 50 EMA, breakout=1, vol_ratio=1.5, deliv=60%
        {'date': '2024-08-14', 'symbol': 'POLYCAB', 'close': 6500, 'return_1d': 2.0, 'return_5d': 5.0, 'return_20d': 10.0, 'ema20': 6200, 'ema50': 6000, 'ema200': 5500, 'volume': 100000, 'avg_volume_20d': 66667, 'volume_ratio': 1.5, 'rs_5d': 3.0, 'rs_20d': 6.0, 'is_breakout_20d': 1, 'above_20ema': 1, 'above_50ema': 1, 'above_200ema': 1, 'dist_ema20': 4.8, 'dist_ema50': 8.3, 'leadership_score': 0},
        # KEI: +4% 1D, +7% 5D, +14% 20D, above 20 & 50 EMA, breakout=1, vol_ratio=2.0, deliv=50%
        {'date': '2024-08-14', 'symbol': 'KEI', 'close': 4200, 'return_1d': 4.0, 'return_5d': 7.0, 'return_20d': 14.0, 'ema20': 4000, 'ema50': 3900, 'ema200': 3500, 'volume': 80000, 'avg_volume_20d': 40000, 'volume_ratio': 2.0, 'rs_5d': 5.0, 'rs_20d': 10.0, 'is_breakout_20d': 1, 'above_20ema': 1, 'above_50ema': 1, 'above_200ema': 1, 'dist_ema20': 5.0, 'dist_ema50': 7.7, 'leadership_score': 0},
        # RRKABEL: -1% 1D, -2% 5D, +2% 20D, below 20 EMA, above 50 EMA, breakout=0, vol_ratio=0.7, deliv=40%
        {'date': '2024-08-14', 'symbol': 'RRKABEL', 'close': 1600, 'return_1d': -1.0, 'return_5d': -2.0, 'return_20d': 2.0, 'ema20': 1650, 'ema50': 1580, 'ema200': 1400, 'volume': 35000, 'avg_volume_20d': 50000, 'volume_ratio': 0.7, 'rs_5d': -4.0, 'rs_20d': -2.0, 'is_breakout_20d': 0, 'above_20ema': 0, 'above_50ema': 1, 'above_200ema': 1, 'dist_ema20': -3.0, 'dist_ema50': 1.2, 'leadership_score': 0},
        # TRENT: +1% 1D, +3% 5D, +8% 20D, above all, breakout=0, vol_ratio=1.0, deliv=45%
        {'date': '2024-08-14', 'symbol': 'TRENT', 'close': 5400, 'return_1d': 1.0, 'return_5d': 3.0, 'return_20d': 8.0, 'ema20': 5200, 'ema50': 5000, 'ema200': 4500, 'volume': 50000, 'avg_volume_20d': 50000, 'volume_ratio': 1.0, 'rs_5d': 1.0, 'rs_20d': 4.0, 'is_breakout_20d': 0, 'above_20ema': 1, 'above_50ema': 1, 'above_200ema': 1, 'dist_ema20': 3.8, 'dist_ema50': 8.0, 'leadership_score': 0}
    ]
    db.insert_or_replace_df("stock_metrics", pd.DataFrame(sm))
    
    # Daily prices for delivery metrics
    dp = [
        {'date': '2024-08-14', 'symbol': 'POLYCAB', 'series': 'EQ', 'close': 6500, 'volume': 100000, 'turnover': 650000000, 'delivery_quantity': 60000, 'delivery_percentage': 60.0},
        {'date': '2024-08-14', 'symbol': 'KEI', 'series': 'EQ', 'close': 4200, 'volume': 80000, 'turnover': 336000000, 'delivery_quantity': 40000, 'delivery_percentage': 50.0},
        {'date': '2024-08-14', 'symbol': 'RRKABEL', 'series': 'EQ', 'close': 1600, 'volume': 35000, 'turnover': 56000000, 'delivery_quantity': 14000, 'delivery_percentage': 40.0},
        {'date': '2024-08-14', 'symbol': 'TRENT', 'series': 'EQ', 'close': 5400, 'volume': 50000, 'turnover': 270000000, 'delivery_quantity': 22500, 'delivery_percentage': 45.0}
    ]
    db.insert_or_replace_df("daily_prices", pd.DataFrame(dp))
    
    calc = IndustryMetricsCalculator(db=db)
    return calc, db


def test_industry_metrics_aggregation(ind_metrics_env):
    calc, db = ind_metrics_env
    
    count = calc.calculate_all_industry_metrics()
    assert count == 2
    
    df_ind = db.get_latest_industry_metrics(trade_date="2024-08-14")
    assert len(df_ind) == 2
    
    wires = df_ind[df_ind['basic_industry'] == 'Wires & Cables'].iloc[0]
    assert wires['stock_count'] == 3
    assert pytest.approx(wires['avg_return_1d'], 0.01) == 1.66667
    assert pytest.approx(wires['ema20_breadth'], 0.01) == 66.66667
    assert pytest.approx(wires['ema50_breadth'], 0.01) == 100.0
    assert pytest.approx(wires['breakout_percentage'], 0.01) == 66.66667
    assert wires['breakout_count'] == 2
    assert pytest.approx(wires['avg_delivery_percentage'], 0.01) == 50.0
    assert wires['is_low_sample'] == 1
