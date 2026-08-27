"""
Unit Tests for Layer 2 Custom Industry & Segment Classification.
Tests:
- Valid CSV synchronization
- Duplicate symbol detection & rejection
- Invalid symbol detection & rejection
- Custom segment query methods
- Separation and preservation of Official NSE classification in stocks table
"""

import pytest
import pandas as pd
from pathlib import Path
from database.db import Database
from pipeline.custom_classification import CustomClassificationResolver


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_custom_app.db"
    db = Database(db_path=db_file)
    db.initialize_schema()

    # Seed mock stocks into stocks table
    mock_stocks = pd.DataFrame([
        {'symbol': 'DIXON', 'company_name': 'Dixon Tech', 'industry': 'Capital Goods', 'basic_industry': 'EMS', 'active': 1},
        {'symbol': 'KAYNES', 'company_name': 'Kaynes Tech', 'industry': 'Capital Goods', 'basic_industry': 'EMS', 'active': 1},
        {'symbol': 'INDHOTEL', 'company_name': 'Indian Hotels', 'industry': 'Consumer Services', 'basic_industry': 'Hotels & Resorts', 'active': 1},
        {'symbol': 'EIHOTEL', 'company_name': 'EIH Ltd', 'industry': 'Consumer Services', 'basic_industry': 'Hotels & Resorts', 'active': 1}
    ])
    db.insert_or_replace_df("stocks", mock_stocks)
    return db


def test_custom_classification_sync_valid(tmp_path, temp_db):
    csv_file = tmp_path / "custom_test.csv"
    csv_file.write_text(
        "symbol,custom_industry,custom_segment,notes\n"
        "DIXON,EMS,Consumer Electronics EMS,Lighting and Consumer\n"
        "KAYNES,EMS,Industrial EMS,Aerospace and Industrial\n"
        "INDHOTEL,Hotels,Luxury / Premium,Taj Hotels\n",
        encoding="utf-8"
    )

    resolver = CustomClassificationResolver(db=temp_db, csv_path=csv_file)
    report = resolver.sync_custom_classifications()

    assert report["status"] == "SUCCESS"
    assert report["rows_read"] == 3
    assert report["valid_count"] == 3
    assert report["invalid_symbols"] == []
    assert report["duplicate_symbols"] == []
    assert report["updated_records"] == 3

    # Check query helpers
    custom_inds = temp_db.get_custom_industries()
    assert sorted(custom_inds) == ["EMS", "Hotels"]

    ems_segments = temp_db.get_custom_segments("EMS")
    assert ems_segments == {"Consumer Electronics EMS": 1, "Industrial EMS": 1}

    df_ems = temp_db.get_stocks_by_custom_industry("EMS")
    assert len(df_ems) == 2
    assert set(df_ems['symbol']) == {"DIXON", "KAYNES"}


def test_custom_classification_rejects_duplicates_and_invalids(tmp_path, temp_db):
    csv_file = tmp_path / "custom_with_errors.csv"
    csv_file.write_text(
        "symbol,custom_industry,custom_segment,notes\n"
        "DIXON,EMS,Consumer Electronics EMS,First occurrence\n"
        "DIXON,EMS,Duplicate EMS,Duplicate row\n"
        "NONEXISTENT,Hotels,Luxury,Not in universe\n"
        "KAYNES,,Missing Industry,Empty industry\n"
        "EIHOTEL,Hotels,Luxury / Premium,Valid row\n",
        encoding="utf-8"
    )

    resolver = CustomClassificationResolver(db=temp_db, csv_path=csv_file)
    report = resolver.sync_custom_classifications()

    assert report["status"] == "SUCCESS"
    assert report["rows_read"] == 5
    assert report["valid_count"] == 2  # DIXON (1st), EIHOTEL
    assert report["duplicate_symbols"] == ["DIXON"]
    assert report["invalid_symbols"] == ["NONEXISTENT"]
    assert report["malformed_rows"] == 1  # KAYNES with missing industry
    assert report["updated_records"] == 2


def test_official_nse_classification_remains_untouched(tmp_path, temp_db):
    # Verify official basic industry before sync
    with temp_db.get_connection() as conn:
        before = conn.execute("SELECT symbol, industry, basic_industry FROM stocks WHERE symbol = 'INDHOTEL';").fetchone()
    assert before[1] == 'Consumer Services'
    assert before[2] == 'Hotels & Resorts'

    # Sync custom classification
    csv_file = tmp_path / "custom_map.csv"
    csv_file.write_text(
        "symbol,custom_industry,custom_segment,notes\n"
        "INDHOTEL,Hotels,Luxury / Premium,Taj Brand\n",
        encoding="utf-8"
    )
    resolver = CustomClassificationResolver(db=temp_db, csv_path=csv_file)
    resolver.sync_custom_classifications()

    # Verify official basic industry after sync is 100% UNTOUCHED
    with temp_db.get_connection() as conn:
        after = conn.execute("SELECT symbol, industry, basic_industry FROM stocks WHERE symbol = 'INDHOTEL';").fetchone()
    assert after[1] == 'Consumer Services'
    assert after[2] == 'Hotels & Resorts'

    # Verify custom layer has separate classification
    with temp_db.get_connection() as conn:
        custom_row = conn.execute("SELECT custom_industry, custom_segment FROM custom_industry_classification WHERE symbol = 'INDHOTEL';").fetchone()
    assert custom_row[0] == 'Hotels'
    assert custom_row[1] == 'Luxury / Premium'
