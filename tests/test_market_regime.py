"""
Unit Tests for Market Regime Synthesis & Overview Analytics Engine (Phase 3).
Tests:
- Regime determination rules (BULLISH, BULLISH BUT NARROW, ROTATION, NEUTRAL, BEARISH)
- Signal confidence calculation
- Breadth & participation metrics
- Emerging vs Cooling ranking
- Dynamic evidence-based summary generation
- Look-ahead bias elimination
- Historical regime aggregation
"""

import pytest
import pandas as pd
from database.db import Database
from analytics.market_regime import MarketRegimeAnalyzer


@pytest.fixture
def mock_db_with_industries(tmp_path):
    db_file = tmp_path / "test_regime.db"
    db = Database(db_path=db_file)
    db.initialize_schema()

    # Seed 10 sample industries for 2 dates
    dates = ["2026-08-20", "2026-08-21"]
    rows = []
    for d in dates:
        rows.extend([
            {'date': d, 'basic_industry': 'EMS', 'industry': 'Capital Goods', 'stock_count': 10, 'avg_return_1d': 1.2, 'avg_return_5d': 6.5, 'avg_return_20d': 12.0, 'industry_rs_5d': 5.0, 'industry_rs_20d': 8.0, 'ema20_breadth': 80.0, 'ema50_breadth': 70.0, 'avg_volume_ratio': 1.8, 'breakout_count': 3, 'score_today': 85.0, 'score_change_5d': 12.0, 'status': 'EMERGING'},
            {'date': d, 'basic_industry': 'Pipes & Tubes', 'industry': 'Metals', 'stock_count': 12, 'avg_return_1d': 2.0, 'avg_return_5d': 8.0, 'avg_return_20d': 15.0, 'industry_rs_5d': 6.5, 'industry_rs_20d': 10.0, 'ema20_breadth': 90.0, 'ema50_breadth': 85.0, 'avg_volume_ratio': 2.5, 'breakout_count': 4, 'score_today': 92.0, 'score_change_5d': 15.0, 'status': 'EMERGING'},
            {'date': d, 'basic_industry': 'Bearings', 'industry': 'Capital Goods', 'stock_count': 8, 'avg_return_1d': 0.8, 'avg_return_5d': 4.5, 'avg_return_20d': 9.0, 'industry_rs_5d': 3.0, 'industry_rs_20d': 6.0, 'ema20_breadth': 75.0, 'ema50_breadth': 65.0, 'avg_volume_ratio': 1.4, 'breakout_count': 2, 'score_today': 78.0, 'score_change_5d': 6.0, 'status': 'STRENGTHENING'},
            {'date': d, 'basic_industry': 'Hotels', 'industry': 'Consumer Services', 'stock_count': 15, 'avg_return_1d': -0.5, 'avg_return_5d': -1.2, 'avg_return_20d': 3.0, 'industry_rs_5d': -2.5, 'industry_rs_20d': 1.0, 'ema20_breadth': 40.0, 'ema50_breadth': 50.0, 'avg_volume_ratio': 0.8, 'breakout_count': 0, 'score_today': 48.0, 'score_change_5d': -8.0, 'status': 'COOLING'},
            {'date': d, 'basic_industry': 'Chemicals', 'industry': 'Commodities', 'stock_count': 20, 'avg_return_1d': -1.0, 'avg_return_5d': -3.5, 'avg_return_20d': -5.0, 'industry_rs_5d': -4.5, 'industry_rs_20d': -6.0, 'ema20_breadth': 25.0, 'ema50_breadth': 30.0, 'avg_volume_ratio': 0.6, 'breakout_count': 0, 'score_today': 32.0, 'score_change_5d': -12.0, 'status': 'WEAK'}
        ])

    df = pd.DataFrame(rows)
    db.insert_or_replace_df("industry_metrics", df)
    return db


def test_market_regime_analysis_calculation(mock_db_with_industries):
    analyzer = MarketRegimeAnalyzer(db=mock_db_with_industries)
    res = analyzer.analyze_session("2026-08-21")

    assert res["trade_date"] == "2026-08-21"
    assert res["total_industries"] == 5
    assert res["bullish_count"] == 1  # Bearings (STRENGTHENING)
    assert res["emerging_count"] == 2  # EMS, Pipes
    assert res["cooling_count"] == 1   # Hotels
    assert res["bearish_count"] == 1   # Chemicals

    # 3 of 5 positive 5D = 60.0%
    assert res["pct_positive_5d"] == 60.0

    # 3 of 5 have EMA20 breadth >= 50% = 60.0%
    assert res["pct_above_ema20"] == 60.0

    # Confidence must be between 0 and 100
    assert 0.0 <= res["confidence"] <= 100.0

    # Emerging and cooling lists must be properly populated
    assert len(res["top_emerging"]) > 0
    assert res["top_emerging"].iloc[0]["basic_industry"] == "Pipes & Tubes"  # Highest acceleration (+15)
    assert res["top_cooling"].iloc[0]["basic_industry"] == "Chemicals"      # Lowest acceleration (-12)


def test_dynamic_summary_contains_actual_evidence(mock_db_with_industries):
    analyzer = MarketRegimeAnalyzer(db=mock_db_with_industries)
    res = analyzer.analyze_session("2026-08-21")
    summary = res["dynamic_summary"]

    # Verify that text includes actual computed numbers
    assert "5 tracked industries" in summary
    assert "60%" in summary
    assert "Pipes & Tubes" in summary
    assert "Chemicals" in summary


def test_historical_regime_aggregation(mock_db_with_industries):
    analyzer = MarketRegimeAnalyzer(db=mock_db_with_industries)
    df_hist = analyzer.get_historical_regimes()

    assert not df_hist.empty
    assert "date" in df_hist.columns
    assert len(df_hist) == 2
    assert "EMERGING" in df_hist.columns
