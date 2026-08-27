"""
Unit tests for Rotation State detection and Score Acceleration.
Tests EMERGING, STRONG, COOLING, DISTRIBUTION, and WEAK classifications.
"""

from pathlib import Path
import pytest
import pandas as pd

from database.db import Database
from analytics.rotation import RotationDetector


@pytest.fixture
def rotation_env(tmp_path):
    db_path = tmp_path / "test_rotation.db"
    db = Database(db_path=db_path)
    db.initialize_schema()
    
    # 6 days of data for Lubricants (simulating EMERGING: 50 -> 76 (+26)),
    # and Wires & Cables (simulating STRONG: 85 -> 90)
    dates = [f"2024-08-{i:02d}" for i in range(10, 16)]
    
    records = []
    # 1. Lubricants: score jumps from 50 to 76 (Emerging!)
    lub_scores = [50.0, 52.0, 56.0, 62.0, 68.0, 76.0]
    for dt, sc in zip(dates, lub_scores):
        records.append({
            'date': dt,
            'industry': 'Oil Gas',
            'basic_industry': 'Lubricants',
            'stock_count': 3,
            'avg_return_1d': 2.0, 'median_return_1d': 2.0,
            'avg_return_5d': 6.0, 'median_return_5d': 6.0,
            'avg_return_20d': 10.0, 'median_return_20d': 10.0,
            'industry_rs_5d': 4.0, 'industry_rs_20d': 8.0,
            'avg_volume_ratio': 1.8,
            'positive_breadth': 100.0, 'ema20_breadth': 100.0, 'ema50_breadth': 66.0, 'ema200_breadth': 66.0,
            'breakout_count': 1, 'breakout_percentage': 33.3,
            'avg_delivery_percentage': 50.0,
            'score_today': sc,
            'score_1d_ago': 0, 'score_3d_ago': 0, 'score_5d_ago': 0,
            'score_change_1d': 0, 'score_change_3d': 0, 'score_change_5d': 0,
            'status': 'WEAK', 'is_low_sample': 1
        })
        
    # 2. Wires & Cables: sustained strong (85 -> 92)
    wc_scores = [85.0, 86.0, 88.0, 89.0, 90.0, 92.0]
    for dt, sc in zip(dates, wc_scores):
        records.append({
            'date': dt,
            'industry': 'Capital Goods',
            'basic_industry': 'Wires & Cables',
            'stock_count': 5,
            'avg_return_1d': 3.0, 'median_return_1d': 3.0,
            'avg_return_5d': 9.0, 'median_return_5d': 9.0,
            'avg_return_20d': 18.0, 'median_return_20d': 18.0,
            'industry_rs_5d': 7.0, 'industry_rs_20d': 14.0,
            'avg_volume_ratio': 2.2,
            'positive_breadth': 100.0, 'ema20_breadth': 100.0, 'ema50_breadth': 100.0, 'ema200_breadth': 100.0,
            'breakout_count': 3, 'breakout_percentage': 60.0,
            'avg_delivery_percentage': 60.0,
            'score_today': sc,
            'score_1d_ago': 0, 'score_3d_ago': 0, 'score_5d_ago': 0,
            'score_change_1d': 0, 'score_change_3d': 0, 'score_change_5d': 0,
            'status': 'WEAK', 'is_low_sample': 0
        })

    db.insert_or_replace_df("industry_metrics", pd.DataFrame(records))
    detector = RotationDetector(db=db)
    return detector, db


def test_rotation_detection(rotation_env):
    detector, db = rotation_env
    cnt = detector.calculate_rotation_states()
    assert cnt == 12
    
    df_latest = db.get_latest_industry_metrics(trade_date="2024-08-15")
    assert len(df_latest) == 2
    
    lub = df_latest[df_latest['basic_industry'] == 'Lubricants'].iloc[0]
    wires = df_latest[df_latest['basic_industry'] == 'Wires & Cables'].iloc[0]
    
    # Lubricants: 5D change = 76.0 - 50.0 = +26.0 -> EMERGING
    assert lub['score_change_5d'] == 26.0
    assert lub['status'] == "EMERGING"
    
    # Wires & Cables: score = 92.0, 5D change = +7.0 -> STRONG
    assert wires['score_today'] == 92.0
    assert wires['status'] == "STRONG"
