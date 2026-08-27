"""
tests/test_decision_ledger.py
Automated Unit and Integrity Tests for the Historical Decision Ledger & Dynamic Retention.
Verifies immutability, zero-overwrite, model version isolation, fast query service,
and calendar-driven dynamic rolling retention.
"""

import pytest
import sqlite3
import pandas as pd
from pathlib import Path

from storage.decision_ledger import DecisionLedger
from storage.decision_ledger_query_service import DecisionLedgerQueryService
from storage.dynamic_retention_service import DynamicRetentionService

@pytest.fixture
def temp_ledger(tmp_path):
    test_db = tmp_path / "test_decision_ledger.db"
    ledger = DecisionLedger(db_path=test_db)
    return ledger, test_db

def test_1_insert_and_retrieve_decision(temp_ledger):
    ledger, db_path = temp_ledger
    records = [{
        "trade_date": "2026-08-09",
        "entity_type": "STOCK",
        "entity_id": "RELIANCE",
        "entity_name": "Reliance Industries Ltd",
        "model_version": "MODEL_V3.2_FROZEN",
        "score": 72.0,
        "rating_action": "BUY",
        "flow_state": "ACCUMULATION",
        "close_price": 2950.0
    }]
    inserted = ledger.record_decisions(records)
    assert inserted == 1

    svc = DecisionLedgerQueryService(db_path=db_path)
    df = svc.get_stock_history("RELIANCE", period="1M")
    assert len(df) == 1
    assert df.iloc[0]["rating_action"] == "BUY"
    assert df.iloc[0]["score"] == 72.0

def test_2_duplicate_insertion_does_not_overwrite(temp_ledger):
    ledger, db_path = temp_ledger
    rec1 = [{
        "trade_date": "2026-08-09",
        "entity_type": "STOCK",
        "entity_id": "RELIANCE",
        "entity_name": "Reliance Industries Ltd",
        "model_version": "MODEL_V3.2_FROZEN",
        "score": 72.0,
        "rating_action": "BUY"
    }]
    ledger.record_decisions(rec1)

    # Attempt to insert different rating for the same date/entity/model
    rec2 = [{
        "trade_date": "2026-08-09",
        "entity_type": "STOCK",
        "entity_id": "RELIANCE",
        "entity_name": "Reliance Industries Ltd",
        "model_version": "MODEL_V3.2_FROZEN",
        "score": 90.0,
        "rating_action": "STRONG_BUY"
    }]
    inserted2 = ledger.record_decisions(rec2)
    assert inserted2 == 0  # Ignored!

    svc = DecisionLedgerQueryService(db_path=db_path)
    df = svc.get_stock_history("RELIANCE", period="1M")
    assert len(df) == 1
    # Historical record MUST remain BUY forever
    assert df.iloc[0]["rating_action"] == "BUY"
    assert df.iloc[0]["score"] == 72.0

def test_3_historical_buy_remains_buy_after_later_strong_buy(temp_ledger):
    ledger, db_path = temp_ledger
    multi_days = [
        {"trade_date": "2026-08-09", "entity_type": "STOCK", "entity_id": "RELIANCE", "score": 72.0, "rating_action": "BUY"},
        {"trade_date": "2026-08-10", "entity_type": "STOCK", "entity_id": "RELIANCE", "score": 75.0, "rating_action": "BUY"},
        {"trade_date": "2026-08-11", "entity_type": "STOCK", "entity_id": "RELIANCE", "score": 82.0, "rating_action": "STRONG_BUY"},
        {"trade_date": "2026-08-12", "entity_type": "STOCK", "entity_id": "RELIANCE", "score": 84.0, "rating_action": "STRONG_BUY"},
        {"trade_date": "2026-08-13", "entity_type": "STOCK", "entity_id": "RELIANCE", "score": 61.0, "rating_action": "WATCH"}
    ]
    ledger.record_decisions(multi_days)

    svc = DecisionLedgerQueryService(db_path=db_path)
    df = svc.get_stock_history("RELIANCE", period="1M")
    assert len(df) == 5
    assert df[df["trade_date"] == "2026-08-09"].iloc[0]["rating_action"] == "BUY"
    assert df[df["trade_date"] == "2026-08-11"].iloc[0]["rating_action"] == "STRONG_BUY"
    assert df[df["trade_date"] == "2026-08-13"].iloc[0]["rating_action"] == "WATCH"

def test_4_model_version_isolation(temp_ledger):
    ledger, db_path = temp_ledger
    v3_rec = [{"trade_date": "2026-08-10", "entity_type": "INDUSTRY", "entity_id": "Steel", "model_version": "MODEL_V3.2_FROZEN", "score": 65.0, "rating_action": "BUY"}]
    v4_rec = [{"trade_date": "2026-08-10", "entity_type": "INDUSTRY", "entity_id": "Steel", "model_version": "MODEL_V4.0_FUTURE", "score": 88.0, "rating_action": "STRONG_BUY"}]
    
    ledger.record_decisions(v3_rec)
    ledger.record_decisions(v4_rec)

    svc = DecisionLedgerQueryService(db_path=db_path)
    df_v3 = svc.get_entity_history("INDUSTRY", "Steel", model_version="MODEL_V3.2_FROZEN")
    df_v4 = svc.get_entity_history("INDUSTRY", "Steel", model_version="MODEL_V4.0_FUTURE")

    assert len(df_v3) == 1 and df_v3.iloc[0]["rating_action"] == "BUY"
    assert len(df_v4) == 1 and df_v4.iloc[0]["rating_action"] == "STRONG_BUY"

def test_5_stock_industry_sector_separation(temp_ledger):
    ledger, db_path = temp_ledger
    recs = [
        {"trade_date": "2026-08-10", "entity_type": "STOCK", "entity_id": "TATASTEEL", "score": 70.0, "rating_action": "BUY"},
        {"trade_date": "2026-08-10", "entity_type": "INDUSTRY", "entity_id": "Steel", "score": 75.0, "rating_action": "BUY"},
        {"trade_date": "2026-08-10", "entity_type": "SECTOR", "entity_id": "METALS", "score": 80.0, "rating_action": "STRONG_BUY"}
    ]
    ledger.record_decisions(recs)

    svc = DecisionLedgerQueryService(db_path=db_path)
    assert len(svc.get_stock_history("TATASTEEL")) == 1
    assert len(svc.get_industry_history("Steel")) == 1
    assert len(svc.get_sector_history("METALS")) == 1

def test_6_row_hash_determinism_and_mutation_detection(temp_ledger):
    ledger, db_path = temp_ledger
    recs = [{"trade_date": "2026-08-10", "entity_type": "STOCK", "entity_id": "INFY", "score": 78.0, "rating_action": "BUY"}]
    ledger.record_decisions(recs)

    # Initial integrity must PASS
    res = ledger.verify_integrity()
    assert res["status"] == "PASS"
    assert res["tampered_records"] == 0

    # Simulate malicious backdoor mutation directly in SQLite fact table
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE fact_historical_decisions SET rating_action = 'STRONG_BUY'")
    conn.commit()
    conn.close()

    # Post-mutation integrity must FAIL
    res_tampered = ledger.verify_integrity()
    assert res_tampered["status"] == "FAIL"
    assert res_tampered["tampered_records"] == 1

def test_7_no_forward_return_columns(temp_ledger):
    ledger, _ = temp_ledger
    with ledger._get_connection() as conn:
        cols = [c[1] for c in conn.execute("PRAGMA table_info(fact_historical_decisions)").fetchall()]
    
    prohibited = ["fwd_return_1d", "fwd_return_5d", "fwd_return_20d", "future_return", "hit_rate", "mae", "mfe"]
    for p in prohibited:
        assert p not in cols, f"Prohibited forward column found: {p}"

def test_8_rating_transitions_detection(temp_ledger):
    ledger, db_path = temp_ledger
    timeline = [
        {"trade_date": "2026-08-01", "entity_type": "STOCK", "entity_id": "TCS", "score": 50.0, "rating_action": "NEUTRAL"},
        {"trade_date": "2026-08-02", "entity_type": "STOCK", "entity_id": "TCS", "score": 55.0, "rating_action": "NEUTRAL"},
        {"trade_date": "2026-08-03", "entity_type": "STOCK", "entity_id": "TCS", "score": 72.0, "rating_action": "BUY"},
        {"trade_date": "2026-08-04", "entity_type": "STOCK", "entity_id": "TCS", "score": 84.0, "rating_action": "STRONG_BUY"}
    ]
    ledger.record_decisions(timeline)

    svc = DecisionLedgerQueryService(db_path=db_path)
    trans = svc.get_rating_transitions("STOCK", "TCS")
    assert len(trans) == 2
    assert trans.iloc[0]["rating_action"] == "BUY" and trans.iloc[0]["prev_rating"] == "NEUTRAL"
    assert trans.iloc[1]["rating_action"] == "STRONG_BUY" and trans.iloc[1]["prev_rating"] == "BUY"

def test_9_dynamic_rolling_retention_resolution():
    retention_svc = DynamicRetentionService()
    res = retention_svc.resolve_hot_operational_window(target_sessions=60)
    assert res["is_dynamic"] is True
    assert res["actual_hot_sessions"] == 60
    assert res["latest_trading_session"] > res["hot_cutoff_session"]

def test_10_dynamic_calendar_progression(tmp_path):
    mock_db = tmp_path / "mock_market.db"
    conn = sqlite3.connect(mock_db)
    conn.execute("CREATE TABLE daily_prices (date TEXT NOT NULL);")
    
    # Insert 65 mock trading dates spanning weekends and holidays
    dates = [f"2026-05-{d:02d}" for d in range(1, 32)] + [f"2026-06-{d:02d}" for d in range(1, 35)]
    conn.executemany("INSERT INTO daily_prices VALUES (?)", [(d,) for d in dates])
    conn.commit()
    conn.close()

    svc = DynamicRetentionService(db_path=mock_db)
    window = svc.resolve_hot_operational_window(target_sessions=60)
    assert window["actual_hot_sessions"] == 60
    assert window["latest_trading_session"] == dates[-1]
    assert window["hot_cutoff_session"] == dates[-60]
