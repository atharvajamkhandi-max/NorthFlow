"""
Unit tests for NSEProvider.
Tests date parsing, data normalization, holiday calendar filtering, and fallback mechanisms.
"""

import datetime
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from providers.nse_provider import NSEProvider


def test_date_formatting():
    provider = NSEProvider()
    
    # ISO to DMY
    assert provider._format_to_dmy("2024-08-14") == "14-08-2024"
    assert provider._format_to_dmy(datetime.date(2024, 8, 14)) == "14-08-2024"
    assert provider._format_to_dmy("14-Aug-2024") == "14-08-2024"
    
    # DMY to ISO
    assert provider._format_to_iso("14-08-2024") == "2024-08-14"
    assert provider._format_to_iso(datetime.date(2024, 8, 14)) == "2024-08-14"
    assert provider._format_to_iso("14-Aug-2024") == "2024-08-14"


def test_parse_delivery_bhavcopy():
    provider = NSEProvider()
    
    mock_data = pd.DataFrame({
        'SYMBOL': ['POLYCAB', 'CASTROLIND', 'GOLD_ETF', 'RELIANCE'],
        'SERIES': ['EQ', 'EQ', 'GS', 'EQ'],
        'DATE1': ['14-Aug-2024', '14-Aug-2024', '14-Aug-2024', '14-Aug-2024'],
        'OPEN_PRICE': ['6500.0', '260.0', '100.0', '2900.0'],
        'HIGH_PRICE': ['6600.0', '265.0', '101.0', '2950.0'],
        'LOW_PRICE': ['6450.0', '258.0', '99.0', '2880.0'],
        'CLOSE_PRICE': ['6550.0', '262.5', '100.5', '2920.0'],
        'PREV_CLOSE': ['6400.0', '255.0', '100.0', '2900.0'],
        'TTL_TRD_QNTY': ['100000', '50000', '1000', '500000'],
        'TURNOVER_LACS': ['6550.0', '131.25', '1.0', '14600.0'],
        'DELIV_QTY': ['45000', '25000', '-', '250000'],
        'DELIV_PER': ['45.0', '50.0', '-', '50.0']
    })
    
    parsed = provider._parse_delivery_bhavcopy(mock_data, "2024-08-14")
    
    # GS series should be filtered out
    assert 'GOLD_ETF' not in parsed['symbol'].values
    assert len(parsed) == 3
    assert set(parsed['symbol'].values) == {'POLYCAB', 'CASTROLIND', 'RELIANCE'}
    
    # Delivery percentage numeric check
    poly = parsed[parsed['symbol'] == 'POLYCAB'].iloc[0]
    assert poly['close'] == 6550.0
    assert poly['delivery_percentage'] == 45.0
    assert poly['turnover'] == 6550.0 * 100000.0


def test_get_trading_days():
    provider = NSEProvider()
    with patch.object(provider, 'get_trading_holidays', return_value=['2024-08-15']):
        # 2024-08-14 (Wed), 2024-08-15 (Thu - Holiday), 2024-08-16 (Fri), 2024-08-17 (Sat), 2024-08-18 (Sun), 2024-08-19 (Mon)
        days = provider.get_trading_days("2024-08-14", "2024-08-19")
        assert '2024-08-15' not in days  # Holiday
        assert '2024-08-17' not in days  # Saturday
        assert '2024-08-18' not in days  # Sunday
        assert '2024-08-14' in days
        assert '2024-08-16' in days
        assert '2024-08-19' in days
