"""
Unit tests for Industry Constituents Drilldown and Override Actions.
Tests get_stocks_by_industry() retrieval of all constituents without truncation,
and verifies override actions (ADD, MOVE, SET, REMOVE).
"""

from pathlib import Path
import pytest
import pandas as pd

from database.db import Database
from pipeline.update_classification import ClassificationUpdater


@pytest.fixture
def constituent_env(tmp_path):
    db_path = tmp_path / "test_constituents.db"
    db = Database(db_path=db_path)
    db.initialize_schema()
    
    # 7 Aluminium stocks
    alu_stocks = [
        {'symbol': 'HINDALCO', 'company_name': 'Hindalco Industries Ltd', 'series': 'EQ', 'industry': 'Metals & Mining', 'basic_industry': 'Aluminium', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'NATIONALUM', 'company_name': 'National Aluminium Co Ltd', 'series': 'EQ', 'industry': 'Metals & Mining', 'basic_industry': 'Aluminium', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'VEDL', 'company_name': 'Vedanta Limited', 'series': 'EQ', 'industry': 'Metals & Mining', 'basic_industry': 'Aluminium', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'MANAKSIA', 'company_name': 'Manaksia Limited', 'series': 'EQ', 'industry': 'Metals & Mining', 'basic_industry': 'Aluminium', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'MAANALU', 'company_name': 'Maan Aluminium Limited', 'series': 'EQ', 'industry': 'Metals & Mining', 'basic_industry': 'Aluminium', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'MANAKALUCO', 'company_name': 'Manaksia Aluminium Company Ltd', 'series': 'EQ', 'industry': 'Metals & Mining', 'basic_industry': 'Aluminium', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'HINDALUMI', 'company_name': 'Hind Aluminium Industries Ltd', 'series': 'EQ', 'industry': 'Metals & Mining', 'basic_industry': 'Aluminium', 'active': 1, 'last_updated': '2024-08-01'}
    ]
    db.insert_or_replace_df("stocks", pd.DataFrame(alu_stocks))
    
    # Metrics
    sm = [
        {'date': '2024-08-14', 'symbol': 'HINDALCO', 'close': 680.0, 'return_1d': 1.5, 'return_5d': 4.2, 'return_20d': 12.0, 'ema20': 650.0, 'ema50': 620.0, 'ema200': 580.0, 'volume': 2000000, 'avg_volume_20d': 1500000, 'volume_ratio': 1.33, 'turnover': 1360000000.0, 'avg_turnover_20d': 975000000.0, 'turnover_ratio': 1.33, 'turnover_quality': 1.33, 'high_proximity': 98.0, 'trend_stack': 100.0, 'rs_5d': 2.0, 'rs_20d': 5.0, 'is_breakout_20d': 1, 'above_20ema': 1, 'above_50ema': 1, 'above_200ema': 1, 'dist_ema20': 4.6, 'dist_ema50': 9.6, 'leadership_score': 85.0},
        {'date': '2024-08-14', 'symbol': 'NATIONALUM', 'close': 180.0, 'return_1d': 2.0, 'return_5d': 6.0, 'return_20d': 15.0, 'ema20': 170.0, 'ema50': 160.0, 'ema200': 140.0, 'volume': 5000000, 'avg_volume_20d': 3000000, 'volume_ratio': 1.66, 'turnover': 900000000.0, 'avg_turnover_20d': 510000000.0, 'turnover_ratio': 1.66, 'turnover_quality': 1.66, 'high_proximity': 99.0, 'trend_stack': 100.0, 'rs_5d': 3.5, 'rs_20d': 8.0, 'is_breakout_20d': 1, 'above_20ema': 1, 'above_50ema': 1, 'above_200ema': 1, 'dist_ema20': 5.8, 'dist_ema50': 12.5, 'leadership_score': 92.0}
    ]
    db.insert_or_replace_df("stock_metrics", pd.DataFrame(sm))
    
    return db


def test_get_stocks_by_industry_all_constituents(constituent_env):
    db = constituent_env
    df_alu = db.get_stocks_by_industry("Aluminium", trade_date="2024-08-14")
    
    # Must return all 7 stocks
    assert len(df_alu) == 7
    symbols = set(df_alu['symbol'].tolist())
    expected = {'HINDALCO', 'NATIONALUM', 'VEDL', 'MANAKSIA', 'MAANALU', 'MANAKALUCO', 'HINDALUMI'}
    assert symbols == expected
    
    # Nationalum has highest leadership score (92), should be first
    assert df_alu.iloc[0]['symbol'] == 'NATIONALUM'
    assert df_alu.iloc[1]['symbol'] == 'HINDALCO'


def test_override_actions_add_move_remove(constituent_env):
    db = constituent_env
    updater = ClassificationUpdater(db=db)
    
    # Move VEDL to 'Mining & Minerals', Remove HINDALUMI
    overrides = [
        {'symbol': 'VEDL', 'industry': 'Metals & Mining', 'basic_industry': 'Mining & Minerals', 'action': 'MOVE'},
        {'symbol': 'HINDALUMI', 'industry': '', 'basic_industry': '', 'action': 'REMOVE'},
        {'symbol': 'NEWALU', 'industry': 'Metals & Mining', 'basic_industry': 'Aluminium', 'action': 'ADD'}
    ]
    
    updater.apply_overrides(overrides)
    
    df_alu = db.get_stocks_by_industry("Aluminium")
    alu_syms = set(df_alu['symbol'].tolist())
    
    assert 'VEDL' not in alu_syms
    assert 'HINDALUMI' not in alu_syms
    assert 'NEWALU' in alu_syms
