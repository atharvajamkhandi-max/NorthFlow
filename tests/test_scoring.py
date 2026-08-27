"""
Unit tests for Money Flow Score and Stock Leadership Scoring.
Tests cross-sectional normalization, weight redistribution on missing delivery, and 0-100 range constraints.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from database.db import Database
from analytics.scoring import MoneyFlowScorer


@pytest.fixture
def scoring_env(tmp_path):
    db_path = tmp_path / "test_scoring.db"
    db = Database(db_path=db_path)
    db.initialize_schema()
    
    # Stocks
    stocks = [
        {'symbol': 'POLYCAB', 'company_name': 'Polycab', 'series': 'EQ', 'industry': 'Capital Goods', 'basic_industry': 'Wires & Cables', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'KEI', 'company_name': 'KEI', 'series': 'EQ', 'industry': 'Capital Goods', 'basic_industry': 'Wires & Cables', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'CASTROLIND', 'company_name': 'Castrol', 'series': 'EQ', 'industry': 'Oil Gas', 'basic_industry': 'Lubricants', 'active': 1, 'last_updated': '2024-08-01'},
        {'symbol': 'SKFINDIA', 'company_name': 'SKF', 'series': 'EQ', 'industry': 'Capital Goods', 'basic_industry': 'Bearings', 'active': 1, 'last_updated': '2024-08-01'}
    ]
    db.insert_or_replace_df("stocks", pd.DataFrame(stocks))
    
    # Industry Metrics for 3 industries
    ind_metrics = [
        # Wires & Cables: Strongest across all dimensions
        {'date': '2024-08-14', 'industry': 'Capital Goods', 'basic_industry': 'Wires & Cables', 'stock_count': 2, 'avg_return_1d': 3.0, 'median_return_1d': 3.0, 'avg_return_5d': 8.0, 'median_return_5d': 8.0, 'avg_return_20d': 15.0, 'median_return_20d': 15.0, 'industry_rs_5d': 6.0, 'industry_rs_20d': 12.0, 'avg_volume_ratio': 2.5, 'positive_breadth': 100.0, 'ema20_breadth': 100.0, 'ema50_breadth': 100.0, 'ema200_breadth': 100.0, 'breakout_count': 2, 'breakout_percentage': 100.0, 'avg_delivery_percentage': 60.0, 'score_today': 0, 'score_1d_ago': 0, 'score_3d_ago': 0, 'score_5d_ago': 0, 'score_change_1d': 0, 'score_change_3d': 0, 'score_change_5d': 0, 'status': 'WEAK', 'is_low_sample': 1},
        # Lubricants: Moderate
        {'date': '2024-08-14', 'industry': 'Oil Gas', 'basic_industry': 'Lubricants', 'stock_count': 1, 'avg_return_1d': 1.0, 'median_return_1d': 1.0, 'avg_return_5d': 3.0, 'median_return_5d': 3.0, 'avg_return_20d': 6.0, 'median_return_20d': 6.0, 'industry_rs_5d': 1.0, 'industry_rs_20d': 3.0, 'avg_volume_ratio': 1.2, 'positive_breadth': 100.0, 'ema20_breadth': 100.0, 'ema50_breadth': 0.0, 'ema200_breadth': 100.0, 'breakout_count': 0, 'breakout_percentage': 0.0, 'avg_delivery_percentage': 40.0, 'score_today': 0, 'score_1d_ago': 0, 'score_3d_ago': 0, 'score_5d_ago': 0, 'score_change_1d': 0, 'score_change_3d': 0, 'score_change_5d': 0, 'status': 'WEAK', 'is_low_sample': 1},
        # Bearings: Weakest
        {'date': '2024-08-14', 'industry': 'Capital Goods', 'basic_industry': 'Bearings', 'stock_count': 1, 'avg_return_1d': -2.0, 'median_return_1d': -2.0, 'avg_return_5d': -4.0, 'median_return_5d': -4.0, 'avg_return_20d': -8.0, 'median_return_20d': -8.0, 'industry_rs_5d': -5.0, 'industry_rs_20d': -10.0, 'avg_volume_ratio': 0.8, 'positive_breadth': 0.0, 'ema20_breadth': 0.0, 'ema50_breadth': 0.0, 'ema200_breadth': 0.0, 'breakout_count': 0, 'breakout_percentage': 0.0, 'avg_delivery_percentage': 30.0, 'score_today': 0, 'score_1d_ago': 0, 'score_3d_ago': 0, 'score_5d_ago': 0, 'score_change_1d': 0, 'score_change_3d': 0, 'score_change_5d': 0, 'status': 'WEAK', 'is_low_sample': 1}
    ]
    db.insert_or_replace_df("industry_metrics", pd.DataFrame(ind_metrics))
    
    # Stock Metrics
    sm = [
        {'date': '2024-08-14', 'symbol': 'POLYCAB', 'close': 6500, 'return_1d': 4.0, 'return_5d': 10.0, 'return_20d': 18.0, 'ema20': 6200, 'ema50': 6000, 'ema200': 5500, 'volume': 100000, 'avg_volume_20d': 50000, 'volume_ratio': 2.0, 'turnover': 650000000.0, 'avg_turnover_20d': 325000000.0, 'turnover_ratio': 2.0, 'turnover_quality': 2.0, 'high_proximity': 98.5, 'trend_stack': 100.0, 'rs_5d': 8.0, 'rs_20d': 14.0, 'is_breakout_20d': 1, 'above_20ema': 1, 'above_50ema': 1, 'above_200ema': 1, 'dist_ema20': 4.8, 'dist_ema50': 8.3, 'leadership_score': 0},
        {'date': '2024-08-14', 'symbol': 'KEI', 'close': 4200, 'return_1d': 2.0, 'return_5d': 6.0, 'return_20d': 12.0, 'ema20': 4000, 'ema50': 3900, 'ema200': 3500, 'volume': 60000, 'avg_volume_20d': 50000, 'volume_ratio': 1.2, 'turnover': 252000000.0, 'avg_turnover_20d': 210000000.0, 'turnover_ratio': 1.2, 'turnover_quality': 1.2, 'high_proximity': 95.0, 'trend_stack': 100.0, 'rs_5d': 4.0, 'rs_20d': 9.0, 'is_breakout_20d': 0, 'above_20ema': 1, 'above_50ema': 1, 'above_200ema': 1, 'dist_ema20': 5.0, 'dist_ema50': 7.7, 'leadership_score': 0}
    ]
    db.insert_or_replace_df("stock_metrics", pd.DataFrame(sm))
    
    scorer = MoneyFlowScorer(db=db)
    return scorer, db


def test_money_flow_and_leadership_scores(scoring_env):
    scorer, db = scoring_env
    
    # 1. Test Industry Money Flow Scoring
    cnt_ind = scorer.calculate_industry_money_flow_scores()
    assert cnt_ind == 3
    
    ind_df = db.get_latest_industry_metrics(trade_date="2024-08-14")
    assert not ind_df.empty
    
    # Verify scores are bounded [0, 100]
    assert (ind_df['score_today'] >= 0.0).all()
    assert (ind_df['score_today'] <= 100.0).all()
    
    # Wires & Cables must have highest score
    wires_row = ind_df[ind_df['basic_industry'] == 'Wires & Cables'].iloc[0]
    bearings_row = ind_df[ind_df['basic_industry'] == 'Bearings'].iloc[0]
    assert wires_row['score_today'] > bearings_row['score_today']
    
    # 2. Test Stock Leadership Scoring
    cnt_sm = scorer.calculate_stock_leadership_scores()
    assert cnt_sm >= 2
    
    with db.get_connection() as conn:
        sm_df = pd.read_sql_query("SELECT * FROM stock_metrics WHERE date = '2024-08-14' ORDER BY leadership_score DESC;", conn)
    
    assert not sm_df.empty
    assert (sm_df['leadership_score'] >= 0.0).all()
    assert (sm_df['leadership_score'] <= 100.0).all()
    
    # Polycab should rank higher than KEI due to stronger near-high, returns, volume ratio, breakout
    polycab = sm_df[sm_df['symbol'] == 'POLYCAB'].iloc[0]
    kei = sm_df[sm_df['symbol'] == 'KEI'].iloc[0]
    assert polycab['leadership_score'] > kei['leadership_score']
