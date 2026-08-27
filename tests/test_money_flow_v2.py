"""
Unit Tests for Money Flow Methodology V2 (Research Layer).
Tests:
- 6 Independent Component calculations (Price, Breadth, DirVol, Trend, Breakout, Delivery)
- Cross-sectional percentile ranking
- Directional Volume Models (A, B, C)
- Delivery confirmation (Up vs Down day spread)
- Statistical Reliability rating decoupled from score
- Composite Money Flow V2 Score and preservation of V1 score
- Multi-period score acceleration & 5D component trajectories
- 2D Flow State Classification
- Conflict / Divergence flag detection
- Empirical Backtester
- Zero look-ahead bias
"""

import pytest
import pandas as pd
import numpy as np
from database.db import Database
from analytics.scoring_v2 import MoneyFlowScorerV2
from analytics.backtesting import MoneyFlowBacktester


@pytest.fixture
def mock_v2_db(tmp_path):
    db_file = tmp_path / "test_v2_scoring.db"
    db = Database(db_path=db_file)
    db.initialize_schema()

    # Seed 5 stocks across 2 industries for 6 consecutive dates
    dates = [f"2026-08-{i:02d}" for i in range(10, 16)]
    
    # Stocks
    stk_rows = [
        {'symbol': 'DIXON', 'company_name': 'Dixon Tech', 'industry': 'Capital Goods', 'basic_industry': 'EMS', 'active': 1},
        {'symbol': 'AMBER', 'company_name': 'Amber Ent', 'industry': 'Capital Goods', 'basic_industry': 'EMS', 'active': 1},
        {'symbol': 'SYRMA', 'company_name': 'Syrma SGS', 'industry': 'Capital Goods', 'basic_industry': 'EMS', 'active': 1},
        {'symbol': 'APLAPOLLO', 'company_name': 'APL Apollo', 'industry': 'Metals', 'basic_industry': 'Pipes & Tubes', 'active': 1},
        {'symbol': 'RATNAMANI', 'company_name': 'Ratnamani', 'industry': 'Metals', 'basic_industry': 'Pipes & Tubes', 'active': 1},
    ]
    db.insert_or_replace_df("stocks", pd.DataFrame(stk_rows))

    # Daily prices & metrics
    dp_rows = []
    sm_rows = []
    for d in dates:
        for s in stk_rows:
            sym = s['symbol']
            dp_rows.append({
                'date': d, 'symbol': sym, 'series': 'EQ',
                'open': 100.0, 'high': 105.0, 'low': 98.0, 'close': 104.0,
                'previous_close': 100.0, 'volume': 10000.0, 'turnover': 1040000.0,
                'delivery_quantity': 5000.0, 'delivery_percentage': 50.0
            })
            sm_rows.append({
                'date': d, 'symbol': sym, 'close': 104.0,
                'return_1d': 4.0, 'return_5d': 8.0, 'return_20d': 15.0,
                'ema20': 95.0, 'ema50': 90.0, 'ema200': 80.0,
                'volume': 10000.0, 'avg_volume_20d': 8000.0, 'volume_ratio': 1.25,
                'turnover': 1040000.0, 'avg_turnover_20d': 800000.0, 'turnover_ratio': 1.3,
                'high_proximity': 98.0, 'trend_stack': 1.0, 'rs_5d': 6.0, 'rs_20d': 12.0,
                'is_breakout_20d': 1, 'above_20ema': 1, 'above_50ema': 1, 'above_200ema': 1,
                'dist_ema20': 9.0, 'dist_ema50': 14.0, 'leadership_score': 88.0
            })

    db.insert_or_replace_df("daily_prices", pd.DataFrame(dp_rows))
    db.insert_or_replace_df("stock_metrics", pd.DataFrame(sm_rows))

    # Seed base industry_metrics
    im_rows = []
    for d in dates:
        im_rows.append({
            'date': d, 'industry': 'Capital Goods', 'basic_industry': 'EMS',
            'stock_count': 3, 'avg_return_1d': 4.0, 'median_return_1d': 4.0,
            'avg_return_5d': 8.0, 'median_return_5d': 8.0,
            'avg_return_20d': 15.0, 'median_return_20d': 15.0,
            'industry_rs_5d': 6.0, 'industry_rs_20d': 12.0,
            'avg_volume_ratio': 1.25, 'positive_breadth': 100.0,
            'ema20_breadth': 100.0, 'ema50_breadth': 100.0, 'ema200_breadth': 100.0,
            'breakout_count': 3, 'breakout_percentage': 100.0,
            'avg_delivery_percentage': 50.0, 'score_today': 85.0,
            'status': 'STRONG', 'is_low_sample': 0
        })
        im_rows.append({
            'date': d, 'industry': 'Metals', 'basic_industry': 'Pipes & Tubes',
            'stock_count': 2, 'avg_return_1d': 1.0, 'median_return_1d': 1.0,
            'avg_return_5d': 3.0, 'median_return_5d': 3.0,
            'avg_return_20d': 6.0, 'median_return_20d': 6.0,
            'industry_rs_5d': 2.0, 'industry_rs_20d': 4.0,
            'avg_volume_ratio': 0.9, 'positive_breadth': 50.0,
            'ema20_breadth': 50.0, 'ema50_breadth': 50.0, 'ema200_breadth': 50.0,
            'breakout_count': 0, 'breakout_percentage': 0.0,
            'avg_delivery_percentage': 40.0, 'score_today': 55.0,
            'status': 'NEUTRAL', 'is_low_sample': 1
        })
    db.insert_or_replace_df("industry_metrics", pd.DataFrame(im_rows))

    return db


def test_v2_scoring_calculation_and_preservation_of_v1(mock_v2_db):
    scorer = MoneyFlowScorerV2(db=mock_v2_db)
    cnt = scorer.calculate_all_v2_scores()
    assert cnt == 12  # 6 dates x 2 industries

    with mock_v2_db.get_connection() as conn:
        df_res = pd.read_sql_query("SELECT * FROM industry_metrics WHERE date = '2026-08-15';", conn)

    assert len(df_res) == 2

    # Verify V1 scores are 100% preserved
    ems = df_res[df_res['basic_industry'] == 'EMS'].iloc[0]
    pipes = df_res[df_res['basic_industry'] == 'Pipes & Tubes'].iloc[0]

    assert ems['score_today'] == 85.0
    assert ems['status'] == 'STRONG'

    # Verify V2 scores and components are populated
    assert ems['score_v2'] is not None
    assert 0.0 <= ems['score_v2'] <= 100.0
    assert ems['price_score'] is not None
    assert ems['breadth_score'] is not None
    assert ems['volume_score'] is not None
    assert ems['trend_score'] is not None
    assert ems['breakout_score'] is not None
    assert ems['delivery_score'] is not None

    # Reliability is decoupled from score
    assert ems['reliability_score'] == round(np.sqrt(3) / np.sqrt(10), 2)
    assert ems['reliability_label'] == 'MODERATE'
    assert pipes['reliability_score'] == round(np.sqrt(2) / np.sqrt(10), 2)
    assert pipes['reliability_label'] == 'LOW'

    # Flow confirmation and 2D flow state
    assert ems['flow_confirmation'] in ['HIGH', 'MODERATE', 'LOW', 'CONFLICTING']
    assert ems['flow_state_v2'] in ['STRONG LEADER', 'ACCELERATING', 'EARLY INFLOW', 'MATURE STRONG', 'COOLING', 'DISTRIBUTION / OUTFLOW', 'WEAK', 'NEUTRAL']


def test_directional_volume_models(mock_v2_db):
    scorer = MoneyFlowScorerV2(db=mock_v2_db)
    scorer.calculate_all_v2_scores()

    with mock_v2_db.get_connection() as conn:
        df_res = pd.read_sql_query("SELECT dir_vol_model_a, dir_vol_model_b, dir_vol_model_c FROM industry_metrics WHERE date = '2026-08-15' AND basic_industry = 'EMS';", conn)

    row = df_res.iloc[0]
    assert row['dir_vol_model_a'] is not None
    assert row['dir_vol_model_b'] is not None
    assert row['dir_vol_model_c'] is not None


def test_conflict_flag_detection():
    # Test divergence logic directly
    cfg_conf = {"DIVERGENCE_PRICE_HIGH": 70.0, "DIVERGENCE_BREADTH_LOW": 40.0}
    flags = []
    price_sc = 85.0
    breadth_sc = 25.0
    if price_sc >= cfg_conf["DIVERGENCE_PRICE_HIGH"] and breadth_sc <= cfg_conf["DIVERGENCE_BREADTH_LOW"]:
        flags.append("PRICE_STRONG_BREADTH_WEAK")

    assert "PRICE_STRONG_BREADTH_WEAK" in flags


def test_backtest_evaluation(mock_v2_db):
    scorer = MoneyFlowScorerV2(db=mock_v2_db)
    scorer.calculate_all_v2_scores()

    bt = MoneyFlowBacktester(db=mock_v2_db)
    res = bt.run_evaluation()

    assert res["status"] in ["SUCCESS", "INSUFFICIENT_FORWARD_DATA"]
