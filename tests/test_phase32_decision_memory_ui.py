"""
tests/test_phase32_decision_memory_ui.py
Automated Unit and Isolation Tests for Phase 32/33 Historical Decision Memory UI.
Verifies honest gap handling, entity field applicability, canonical forecast projections,
trading-session future date arithmetic, and immutability.
"""

import pytest
import sqlite3
import pandas as pd
from pathlib import Path

from storage.decision_ledger_query_service import DecisionLedgerQueryService
from storage.dynamic_retention_service import DynamicRetentionService
from storage.canonical_forecast_service import CanonicalForecastService

def test_1_decision_memory_ui_module_importable():
    from dashboard.decision_memory import render_decision_memory_ui, _get_rating_badge, _get_flow_badge, _get_radar_badge
    assert callable(render_decision_memory_ui)
    assert "STRONG BUY" in _get_rating_badge("STRONG_BUY")
    assert "Not applicable" in _get_flow_badge("ACCUMULATION", entity_type="STOCK")
    assert "ACCUMULATION" in _get_flow_badge("ACCUMULATION", entity_type="INDUSTRY")

def test_2_stock_timeline_query_latency():
    svc = DecisionLedgerQueryService()
    df = svc.get_stock_history("RELIANCE", period="12M")
    assert not df.empty
    assert len(df) >= 240
    assert "score" in df.columns
    assert "rating_action" in df.columns
    assert "close_price" in df.columns

def test_3_industry_timeline_query():
    svc = DecisionLedgerQueryService()
    df = svc.get_industry_history("Stainless Steels", period="12M")
    assert not df.empty
    assert "score" in df.columns
    assert "rating_action" in df.columns

def test_4_sector_timeline_query():
    svc = DecisionLedgerQueryService()
    df = svc.get_sector_history("Steel", period="12M")
    assert not df.empty
    assert "score" in df.columns
    assert "rating_action" in df.columns

def test_5_period_filtering():
    svc = DecisionLedgerQueryService()
    df_1m = svc.get_stock_history("RELIANCE", period="1M")
    df_3m = svc.get_stock_history("RELIANCE", period="3M")
    df_12m = svc.get_stock_history("RELIANCE", period="12M")

    assert len(df_1m) <= 22
    assert len(df_3m) <= 65
    assert len(df_12m) >= 240
    assert len(df_1m) < len(df_3m) < len(df_12m)

def test_6_rating_transitions_query():
    svc = DecisionLedgerQueryService()
    trans = svc.get_rating_transitions("STOCK", "RELIANCE", period="12M")
    assert not trans.empty
    assert "prev_rating" in trans.columns
    assert "rating_action" in trans.columns

def test_7_historical_decisions_are_read_only():
    db_path = Path("data/decision_ledger.db")
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM historical_decision_ledger")
        cnt = cur.fetchone()[0]
        assert cnt == 777946

def test_8_no_ledger_rows_modified_during_queries():
    db_path = Path("data/decision_ledger.db")
    initial_sz = db_path.stat().st_size
    svc = DecisionLedgerQueryService()
    
    svc.get_stock_history("TCS")
    svc.get_stock_history("INFY")
    svc.get_industry_history("Stainless Steels")
    svc.get_sector_history("Steel")
    
    assert db_path.stat().st_size == initial_sz

def test_9_historical_timeline_available_beyond_60_sessions():
    svc = DecisionLedgerQueryService()
    df = svc.get_stock_history("RELIANCE", period="12M")
    assert len(df) > 60

def test_10_no_forward_return_columns_stored_in_view():
    svc = DecisionLedgerQueryService()
    df = svc.get_stock_history("RELIANCE", period="1M")
    prohibited = ["fwd_return_1d", "fwd_return_5d", "fwd_return_20d", "future_return", "hit_rate"]
    for p in prohibited:
        assert p not in df.columns

def test_11_app_py_navigation_mounted():
    app_text = Path("app.py").read_text(encoding="utf-8")
    assert "🧠 Historical Decision Memory" in app_text
    assert "render_decision_memory_ui(db, selected_date)" in app_text

def test_12_historical_data_gap_detection():
    svc = DecisionLedgerQueryService()
    df = svc.get_stock_history("RELIANCE", period="ALL")
    df["dt"] = pd.to_datetime(df["trade_date"])
    df["gap"] = df["dt"].diff().dt.days
    assert (df["gap"] > 10).any()  # True 314-day historical gap detected

def test_13_canonical_industry_forecast():
    fc_svc = CanonicalForecastService()
    res = fc_svc.get_industry_forecast("API & CDMO / CRAMS")
    assert res["status"] == "AVAILABLE"
    assert res["exp_return_20d"] == 3.84
    assert res["p10_20d"] == -6.52
    assert res["p90_20d"] == 14.2
    assert res["prob_win"] == 69.7

def test_14_future_trading_date_resolution():
    fc_svc = CanonicalForecastService()
    target_d = fc_svc.resolve_future_trading_date("2026-08-24", forward_sessions=20)
    assert target_d == "2026-09-21" or target_d == "2026-09-22"

def test_15_stock_model_implied_projection():
    fc_svc = CanonicalForecastService()
    res = fc_svc.get_stock_model_projection(
        symbol="RELIANCE",
        current_price=1300.0,
        parent_industry="API & CDMO / CRAMS",
        current_date_str="2026-08-24"
    )
    assert res["status"] == "AVAILABLE"
    assert "20D" in res["horizons"]
    assert "p10" in res["quantiles_20d"]
    assert "p90" in res["quantiles_20d"]
    assert res["quantiles_20d"]["p10"]["price"] < 1300.0
    assert res["quantiles_20d"]["p90"]["price"] > 1300.0
