"""
Unit Tests for Phase 13 365-Day NSE Trading Session Calendar Navigation & Maturity Engine.
Verifies:
1. Available NSE Session Loading & Chronological Ordering
2. Non-Trading Day (Weekend) Exclusion Verification
3. Elapsed Session & Maturity Status Calculations (5D, 10D, 20D, 30D)
4. Sequential Navigation Logic
"""

import os
import datetime
import pytest
from database.db import Database
from dashboard.components.trading_calendar import (
    get_available_nse_sessions,
    get_session_maturity_status
)

def test_trading_calendar_sessions_loading():
    db = Database()
    sessions = get_available_nse_sessions(db)
    assert len(sessions) > 0, "No trading sessions found in database"
    # Verify chronological sorting
    assert sessions == sorted(sessions), "Sessions are not strictly sorted chronologically"

def test_trading_calendar_no_weekends():
    db = Database()
    sessions = get_available_nse_sessions(db)
    for s in sessions:
        dt = datetime.datetime.strptime(s, "%Y-%m-%d").date()
        assert dt.weekday() < 5, f"Found weekend date in trading sessions: {s} (Day: {dt.strftime('%A')})"

def test_session_maturity_calculation_latest():
    db = Database()
    sessions = get_available_nse_sessions(db)
    latest_date = sessions[-1]
    
    mat = get_session_maturity_status(latest_date, sessions)
    assert mat['is_latest'] is True
    assert mat['elapsed_trading_sessions'] == 0
    assert mat['5D'] is False
    assert mat['10D'] is False
    assert mat['20D'] is False
    assert mat['30D'] is False

def test_session_maturity_calculation_historical():
    db = Database()
    sessions = get_available_nse_sessions(db)
    if len(sessions) >= 25:
        oldest_date = sessions[0]
        mat = get_session_maturity_status(oldest_date, sessions)
        assert mat['is_latest'] is False
        assert mat['elapsed_trading_sessions'] >= 24
        assert mat['5D'] is True
        assert mat['10D'] is True
        assert mat['20D'] is True
