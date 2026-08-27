"""
Unit tests for Industry Classification Resolution Hierarchy.
Tests priority ordering: Overrides > Seed > Index > UNKNOWN.
"""

import tempfile
from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from database.db import Database
from providers.nse_provider import NSEProvider
from pipeline.update_classification import ClassificationUpdater


@pytest.fixture
def test_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_class.db"
        db = Database(db_path=db_path)
        db.initialize_schema()
        
        provider = MagicMock(spec=NSEProvider)
        updater = ClassificationUpdater(db=db, provider=provider)
        yield updater, db, provider


def test_classification_priority_resolution(test_env):
    updater, db, provider = test_env
    
    # Mock universe of 4 stocks
    provider.get_security_universe.return_value = pd.DataFrame([
        {'symbol': 'POLYCAB', 'company_name': 'Polycab India', 'series': 'EQ', 'isin': 'INE455K01017'},
        {'symbol': 'HAL', 'company_name': 'Hindustan Aeronautics', 'series': 'EQ', 'isin': 'INE066F01012'},
        {'symbol': 'NIFTY_STOCK', 'company_name': 'Some Index Stock', 'series': 'EQ', 'isin': 'INE123A01011'},
        {'symbol': 'NEW_IPO', 'company_name': 'Brand New IPO', 'series': 'EQ', 'isin': 'INE999A01099'}
    ])
    
    # Overrides: POLYCAB overridden to Custom Wires
    overrides_df = pd.DataFrame([
        {'symbol': 'POLYCAB', 'industry': 'Overridden Industry', 'basic_industry': 'Custom Wires & Cables'}
    ])
    
    # Seed: HAL in seed
    seed_dict = {
        'HAL': {'industry': 'Capital Goods', 'basic_industry': 'Aerospace & Defence'}
    }
    
    # Index: NIFTY_STOCK in index
    index_dict = {
        'NIFTY_STOCK': {'industry': 'Financial Services', 'basic_industry': 'Financial Services'}
    }
    
    with patch.object(updater, 'load_user_overrides', return_value=overrides_df),          patch.object(updater, 'load_seed_classifications', return_value=seed_dict),          patch.object(updater, 'fetch_nse_index_classifications', return_value=index_dict):
        
        count = updater.sync_universe_and_classifications()
        assert count == 4
        
        stocks = db.get_active_stocks()
        
        # 1. POLYCAB should come from Overrides
        poly = stocks[stocks['symbol'] == 'POLYCAB'].iloc[0]
        assert poly['basic_industry'] == 'Custom Wires & Cables'
        assert poly['industry'] == 'Overridden Industry'
        
        # 2. HAL should come from Seed
        hal = stocks[stocks['symbol'] == 'HAL'].iloc[0]
        assert hal['basic_industry'] == 'Aerospace & Defence'
        
        # 3. NIFTY_STOCK should come from Index
        nifty_stk = stocks[stocks['symbol'] == 'NIFTY_STOCK'].iloc[0]
        assert nifty_stk['basic_industry'] == 'Financial Services'
        
        # 4. NEW_IPO should be UNKNOWN
        ipo = stocks[stocks['symbol'] == 'NEW_IPO'].iloc[0]
        assert ipo['basic_industry'] == 'UNKNOWN'
        assert ipo['industry'] == 'UNKNOWN'
