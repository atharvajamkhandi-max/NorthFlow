"""
Unit tests for Market Data Updater.
Tests single-date ingestion, backfill resumption, duplicate prevention, and benchmark sync.
"""

import tempfile
from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from database.db import Database
from providers.nse_provider import NSEProvider
from pipeline.update_market_data import MarketDataUpdater


@pytest.fixture
def test_updater_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_market_update.db"
        db = Database(db_path=db_path)
        db.initialize_schema()
        
        provider = MagicMock(spec=NSEProvider)
        provider._format_to_iso.side_effect = lambda x: str(x)
        provider.get_trading_days.return_value = ["2024-08-13", "2024-08-14"]
        
        updater = MarketDataUpdater(db=db, provider=provider)
        yield updater, db, provider


def test_resumable_ingest_skips_existing(test_updater_env):
    updater, db, provider = test_updater_env
    
    # Pre-populate 2024-08-13
    df_existing = pd.DataFrame([{
        'date': '2024-08-13',
        'symbol': 'POLYCAB',
        'series': 'EQ',
        'open': 6400.0,
        'high': 6500.0,
        'low': 6350.0,
        'close': 6450.0,
        'previous_close': 6400.0,
        'volume': 50000.0,
        'turnover': 322500000.0,
        'delivery_quantity': 25000.0,
        'delivery_percentage': 50.0
    }])
    db.insert_or_replace_df("daily_prices", df_existing)
    
    # Mock data for 2024-08-14
    df_new = pd.DataFrame([{
        'date': '2024-08-14',
        'symbol': 'POLYCAB',
        'series': 'EQ',
        'open': 6450.0,
        'high': 6600.0,
        'low': 6450.0,
        'close': 6550.0,
        'previous_close': 6450.0,
        'volume': 60000.0,
        'turnover': 393000000.0,
        'delivery_quantity': 30000.0,
        'delivery_percentage': 50.0
    }])
    provider.get_daily_equity_data.return_value = df_new
    provider.get_index_data.return_value = pd.DataFrame([
        {'date': '2024-08-13', 'index_name': 'NIFTY 50', 'open': 24000.0, 'high': 24100.0, 'low': 23950.0, 'close': 24050.0, 'volume': 100000.0, 'turnover': 1000000.0},
        {'date': '2024-08-14', 'index_name': 'NIFTY 50', 'open': 24050.0, 'high': 24200.0, 'low': 24000.0, 'close': 24180.0, 'volume': 120000.0, 'turnover': 1200000.0}
    ])
    
    res = updater.backfill_date_range("2024-08-13", "2024-08-14")
    
    # 2024-08-13 should NOT be called via get_daily_equity_data (resumed)
    provider.get_daily_equity_data.assert_called_once_with("2024-08-14")
    assert res["missing_dates_downloaded"] == 1
    assert res["records_inserted"] == 1
    
    # Verify both dates exist in DB
    dates = db.get_existing_price_dates()
    assert sorted(dates) == ["2024-08-13", "2024-08-14"]
