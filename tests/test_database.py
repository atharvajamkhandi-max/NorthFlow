"""
Unit tests for SQLite database schema, CRUD methods, constraints, and duplicate prevention.
"""

import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from database.db import Database


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_market.db"
        db = Database(db_path=db_path)
        db.initialize_schema()
        yield db


def test_schema_initialization(temp_db):
    assert temp_db.db_path.exists()
    stats = temp_db.get_data_health_stats()
    assert stats["total_stocks"] == 0
    assert stats["total_price_records"] == 0


def test_stocks_crud_and_upsert(temp_db):
    df_stocks = pd.DataFrame([
        {
            "symbol": "POLYCAB",
            "company_name": "Polycab India Limited",
            "isin": "INE455K01017",
            "series": "EQ",
            "industry": "Capital Goods",
            "basic_industry": "Wires & Cables",
            "active": 1,
            "last_updated": "2024-08-14 10:00:00"
        },
        {
            "symbol": "CASTROLIND",
            "company_name": "Castrol India Limited",
            "isin": "INE172A01027",
            "series": "EQ",
            "industry": "Oil Gas & Consumable Fuels",
            "basic_industry": "Lubricants",
            "active": 1,
            "last_updated": "2024-08-14 10:00:00"
        }
    ])
    
    # Insert
    temp_db.insert_or_replace_df("stocks", df_stocks)
    active = temp_db.get_active_stocks()
    assert len(active) == 2
    assert "POLYCAB" in active["symbol"].values
    
    # Upsert with modified basic_industry
    df_stocks.loc[df_stocks["symbol"] == "POLYCAB", "basic_industry"] = "Cables - Electricals"
    temp_db.insert_or_replace_df("stocks", df_stocks)
    
    active_after = temp_db.get_active_stocks()
    assert len(active_after) == 2
    poly = active_after[active_after["symbol"] == "POLYCAB"].iloc[0]
    assert poly["basic_industry"] == "Cables - Electricals"


def test_daily_prices_unique_constraint(temp_db):
    df_prices = pd.DataFrame([
        {
            "date": "2024-08-14",
            "symbol": "POLYCAB",
            "series": "EQ",
            "open": 6500.0,
            "high": 6600.0,
            "low": 6450.0,
            "close": 6550.0,
            "previous_close": 6400.0,
            "volume": 100000.0,
            "turnover": 655000000.0,
            "delivery_quantity": 45000.0,
            "delivery_percentage": 45.0
        }
    ])
    
    # Insert once
    temp_db.insert_or_replace_df("daily_prices", df_prices)
    dates = temp_db.get_existing_price_dates()
    assert dates == ["2024-08-14"]
    
    # Insert same date/symbol again (idempotent upsert)
    df_prices_updated = df_prices.copy()
    df_prices_updated["close"] = 6560.0
    temp_db.insert_or_replace_df("daily_prices", df_prices_updated)
    
    prices = temp_db.get_daily_prices(start_date="2024-08-14", end_date="2024-08-14")
    assert len(prices) == 1
    assert prices.iloc[0]["close"] == 6560.0


def test_null_delivery_preservation(temp_db):
    # Ensure missing delivery values are stored as NULL (None / NaN) not 0.0
    df_prices = pd.DataFrame([
        {
            "date": "2024-08-14",
            "symbol": "UNKNOWN_STOCK",
            "series": "EQ",
            "open": 100.0,
            "high": 105.0,
            "low": 98.0,
            "close": 102.0,
            "previous_close": 100.0,
            "volume": 5000.0,
            "turnover": 510000.0,
            "delivery_quantity": np.nan,
            "delivery_percentage": np.nan
        }
    ])
    
    temp_db.insert_or_replace_df("daily_prices", df_prices)
    prices = temp_db.get_daily_prices()
    row = prices.iloc[0]
    assert pd.isna(row["delivery_percentage"])
