"""
Unit Tests for Daily NSE Data Pipeline 4-Checkpoint Schedule & Idempotency.
Tests:
- Scenario 1: 5:00 PM data available -> Process, 6/7/8 PM skipped due to idempotency
- Scenario 2: 5:00 PM unavailable -> 6:00 PM available -> Process, 7/8 PM skipped
- Scenario 3: 5/6/7 PM unavailable -> 8:00 PM available -> Process -> SUCCESS
- Scenario 4: 5/6/7/8 PM unavailable -> FAILED / DATA STALE after final 20:00 attempt
- Non-trading day (weekend/holiday) skip
"""

import pytest
import datetime
from unittest.mock import MagicMock
import pandas as pd
from database.db import Database
from pipeline.daily_runner import DailyPipelineRunner


@pytest.fixture
def mock_pipeline_env(tmp_path):
    db_file = tmp_path / "test_schedule.db"
    db = Database(db_path=db_file)
    db.initialize_schema()

    # Seed basic stock
    df_stocks = pd.DataFrame([
        {'symbol': 'DIXON', 'company_name': 'Dixon Tech', 'industry': 'Capital Goods', 'basic_industry': 'EMS', 'active': 1}
    ])
    db.insert_or_replace_df("stocks", df_stocks)

    mock_provider = MagicMock()
    # Mock trading days: treat 2026-08-24 (Monday) as a valid trading day
    mock_provider.get_trading_days.return_value = ["2026-08-24"]
    mock_provider._format_to_iso.side_effect = lambda d: str(d)

    return db, mock_provider


def test_scenario_1_5pm_available_then_subsequent_skipped(mock_pipeline_env):
    """
    Scenario 1: 5:00 PM data available -> Ingests & processes -> 6, 7, 8 PM skipped as already success.
    """
    db, provider = mock_pipeline_env
    runner = DailyPipelineRunner(db=db, provider=provider)
    trade_date = "2026-08-24"

    # Mock provider returning valid price data for 5 PM
    df_price = pd.DataFrame([{
        'date': trade_date, 'symbol': 'DIXON', 'series': 'EQ',
        'open': 14800.0, 'high': 15000.0, 'low': 14750.0, 'close': 14950.0,
        'previous_close': 14700.0, 'volume': 50000.0, 'turnover': 747500000.0,
        'delivery_quantity': 25000.0, 'delivery_percentage': 50.0
    }])
    provider.get_daily_equity_data.return_value = df_price
    provider.get_index_data.return_value = pd.DataFrame([{'date': trade_date, 'close': 18000.0, 'open': 17900.0, 'high': 18050.0, 'low': 17850.0}])

    # 1. Checkpoint 17:00 IST -> Data available -> SUCCESS
    res_17 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="17:00")
    assert res_17["status"] == "SUCCESS"
    assert res_17["records_processed"] == 1

    # 2. Checkpoint 18:00 IST -> Should detect idempotency and SKIP immediately
    res_18 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="18:00")
    assert res_18["status"] == "SKIPPED_ALREADY_SUCCESS"

    # 3. Checkpoint 19:00 IST -> Should SKIP immediately
    res_19 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="19:00")
    assert res_19["status"] == "SKIPPED_ALREADY_SUCCESS"

    # 4. Checkpoint 20:00 IST -> Should SKIP immediately
    res_20 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="20:00")
    assert res_20["status"] == "SKIPPED_ALREADY_SUCCESS"


def test_scenario_2_5pm_unavailable_6pm_available(mock_pipeline_env):
    """
    Scenario 2: 5:00 PM unavailable (RETRY_PENDING) -> 6:00 PM available (SUCCESS) -> 7/8 PM skipped.
    """
    db, provider = mock_pipeline_env
    runner = DailyPipelineRunner(db=db, provider=provider)
    trade_date = "2026-08-24"

    # 1. At 17:00, NSE returns empty dataframe (not ready)
    provider.get_daily_equity_data.return_value = pd.DataFrame()
    res_17 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="17:00")
    assert res_17["status"] == "RETRY_PENDING"

    # 2. At 18:00, NSE bhavcopy is ready
    df_price = pd.DataFrame([{
        'date': trade_date, 'symbol': 'DIXON', 'series': 'EQ',
        'open': 14800.0, 'high': 15000.0, 'low': 14750.0, 'close': 14950.0,
        'previous_close': 14700.0, 'volume': 50000.0, 'turnover': 747500000.0,
        'delivery_quantity': 25000.0, 'delivery_percentage': 50.0
    }])
    provider.get_daily_equity_data.return_value = df_price
    provider.get_index_data.return_value = pd.DataFrame([{'date': trade_date, 'close': 18000.0, 'open': 17900.0, 'high': 18050.0, 'low': 17850.0}])

    res_18 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="18:00")
    assert res_18["status"] == "SUCCESS"

    # 3. Subsequent checkpoints 19:00 & 20:00 skipped
    res_19 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="19:00")
    assert res_19["status"] == "SKIPPED_ALREADY_SUCCESS"


def test_scenario_3_retry_until_final_8pm_success(mock_pipeline_env):
    """
    Scenario 3: 5, 6, 7 PM unavailable -> 8:00 PM available -> SUCCESS.
    """
    db, provider = mock_pipeline_env
    runner = DailyPipelineRunner(db=db, provider=provider)
    trade_date = "2026-08-24"

    # Unavailable for 17:00, 18:00, 19:00
    provider.get_daily_equity_data.return_value = pd.DataFrame()
    assert runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="17:00")["status"] == "RETRY_PENDING"
    assert runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="18:00")["status"] == "RETRY_PENDING"
    assert runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="19:00")["status"] == "RETRY_PENDING"

    # Available at 20:00
    df_price = pd.DataFrame([{
        'date': trade_date, 'symbol': 'DIXON', 'series': 'EQ',
        'open': 14800.0, 'high': 15000.0, 'low': 14750.0, 'close': 14950.0,
        'previous_close': 14700.0, 'volume': 50000.0, 'turnover': 747500000.0,
        'delivery_quantity': 25000.0, 'delivery_percentage': 50.0
    }])
    provider.get_daily_equity_data.return_value = df_price
    provider.get_index_data.return_value = pd.DataFrame([{'date': trade_date, 'close': 18000.0, 'open': 17900.0, 'high': 18050.0, 'low': 17850.0}])

    res_20 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="20:00")
    assert res_20["status"] == "SUCCESS"


def test_scenario_4_all_checkpoints_fail_stops_at_8pm(mock_pipeline_env):
    """
    Scenario 4: 17:00, 18:00, 19:00 unavailable -> 20:00 unavailable -> FAILED / DATA STALE.
    """
    db, provider = mock_pipeline_env
    runner = DailyPipelineRunner(db=db, provider=provider)
    trade_date = "2026-08-24"

    provider.get_daily_equity_data.return_value = pd.DataFrame()

    res_17 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="17:00")
    assert res_17["status"] == "RETRY_PENDING"

    res_18 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="18:00")
    assert res_18["status"] == "RETRY_PENDING"

    res_19 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="19:00")
    assert res_19["status"] == "RETRY_PENDING"

    # Final attempt at 20:00 fails -> marks FAILED and stops retrying
    res_20 = runner.run_checkpoint(target_date=trade_date, checkpoint_time_str="20:00")
    assert res_20["status"] == "FAILED"
    assert "PIPELINE FAILED / DATA STALE" in res_20["message"]


def test_weekend_holiday_skip(mock_pipeline_env):
    """
    Checks that non-trading days (weekends / holidays) are skipped.
    """
    db, provider = mock_pipeline_env
    runner = DailyPipelineRunner(db=db, provider=provider)

    # 2026-08-23 is Sunday
    sunday = datetime.date(2026, 8, 23)
    res = runner.run_checkpoint(target_date=sunday, checkpoint_time_str="17:00")
    assert res["status"] == "SKIPPED_NOT_TRADING_DAY"
