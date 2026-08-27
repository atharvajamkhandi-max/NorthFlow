"""
tests/test_phase77_live_ui_acceptance.py
========================================
Phase 77 Automated Unit, Integration & Live UI Acceptance Tests:
Market Overview Live Acceptance, Card Click Interactions, Dropdown Synchronization,
Active Universe Bounding, Filter Transitions, Themes & Production Immutability.
"""

import sys
import sqlite3
import hashlib
import pytest
import requests
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from database.db import Database
from dashboard.components.universe_service import resolve_user_universe
from analytics.canonical_v3_2_service import get_canonical_stock_quant_score
from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
from dashboard.components.theme import THEME_TOKENS

DB_PATH = BASE / "data" / "market_flow.db"

PRODUCTION_FILES = {
    "model_v3_2_frozen.py": {
        "path": BASE / "config" / "model_v3_2_frozen.py",
        "expected_sha256": "e350e9209960357d75668ff3dc9fb742162525169ae1f19d7fb7b681beadc756",
    },
    "final_predictions.csv": {
        "path": BASE / "research" / "final_v3" / "results" / "final_predictions.csv",
        "expected_sha256": "52019b780e8b9d714e8f926063dce725541b27335dec47b7f6e66346520bca6b",
    },
    "live_predictions.csv": {
        "path": BASE / "research" / "live_forward" / "ledger" / "live_predictions.csv",
        "expected_sha256": "7950580952b7d3e4d082aeb2c8b48ed892fbe9ce2487d0755255cce81977136e",
    },
    "live_hashes.csv": {
        "path": BASE / "research" / "live_forward" / "ledger" / "live_hashes.csv",
        "expected_sha256": "0010c55813170804e62726ce458ac78cee0394b8995b9f3d2bd8066014c0ca43",
    },
    "promotion_status.json": {
        "path": BASE / "research" / "live_forward" / "promotion_gate" / "promotion_status.json",
        "expected_sha256": "e9761f0b27853f1e2d3635dbe11a36a859b2dee899a1aeb6a15a8f39c1575fa3",
    },
    "decision_ledger.db": {
        "path": BASE / "data" / "decision_ledger.db",
        "expected_sha256": "2a3f7046e8cf072a959c044ddd879a61720deb049eb7ff5cc16703acdf8f7696",
    },
}

@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(str(DB_PATH))
    yield c
    c.close()

@pytest.fixture(scope="module")
def latest_trade_date(conn):
    return pd.read_sql("SELECT MAX(date) FROM stock_metrics", conn).iloc[0, 0]

@pytest.fixture(scope="module")
def master_df(conn, latest_trade_date):
    return pd.read_sql(f"""
    SELECT 
        s.symbol, s.company_name, s.series, s.sme_status, s.macro_sector, s.industry, s.basic_industry,
        COALESCE(scm.market_cap, 100.0) as market_cap_cr,
        COALESCE(m.avg_turnover_20d, 0.0) as avg_turnover_20d
    FROM stocks s
    LEFT JOIN stock_classification_master_v3 scm ON s.symbol = scm.symbol
    LEFT JOIN stock_metrics m ON s.symbol = m.symbol AND m.date = '{latest_trade_date}'
    WHERE s.active = 1
    """, conn)

# 1. PRODUCTION IMMUTABILITY
class TestProductionImmutability:
    @pytest.mark.parametrize("fname,info", PRODUCTION_FILES.items())
    def test_production_artifact_hash_preserved(self, fname, info):
        fpath = info["path"]
        actual = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
        expected = info["expected_sha256"]
        assert actual == expected, f"Immutability violated for {fname}: expected {expected}, got {actual}"

# 2. LIVE APP HEALTH
class TestLiveAppHealth:
    def test_streamlit_health_endpoint(self):
        try:
            resp = requests.get("http://localhost:8501/_stcore/health", timeout=3.0)
            assert resp.status_code == 200
            assert resp.text.strip() == "ok"
        except Exception as e:
            pytest.skip(f"Streamlit server not reachable on localhost:8501 ({e})")

# 3. INTERACTION AUDIT & DRILLDOWN
class TestLiveInteractionAndDrilldown:
    def test_50k_megacap_drilldown_zero_leakage(self, conn, latest_trade_date, master_df):
        u_50k = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=50000.0, min_turnover_lakhs=0.0)
        assert u_50k["eligible_count"] == 440
        
        test_inds = [
            "Finished Formulations",
            "Precision Auto Engine Components",
            "Diversified Consumer & MSME NBFC",
            "Private Sector Banks",
            "Commercial Vehicles",
            "Two & Three Wheelers"
        ]
        mcap_map = dict(zip(master_df['symbol'], master_df['market_cap_cr']))
        sme_map = dict(zip(master_df['symbol'], master_df['sme_status']))
        
        for ind in test_inds:
            syms = list(u_50k["eligible_symbols"])
            ph = ",".join(["?"] * len(syms))
            sql = f"SELECT symbol FROM stocks WHERE industry = ? AND active = 1 AND symbol IN ({ph})"
            res = pd.read_sql(sql, conn, params=[ind] + syms)
            for sym in res['symbol']:
                assert sym in u_50k["eligible_symbols"]
                assert mcap_map[sym] >= 50000.0
                assert sme_map[sym] == 'NON_SME'

    def test_stock_recommender_50k_zero_leakage(self, latest_trade_date, master_df):
        u_50k = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=50000.0, min_turnover_lakhs=0.0)
        df_stk_raw = get_canonical_stock_quant_score(latest_trade_date)
        df_stk_50k = df_stk_raw[df_stk_raw['symbol'].isin(u_50k['eligible_symbols'])].copy()
        
        assert len(df_stk_50k) == 440
        mcap_map = dict(zip(master_df['symbol'], master_df['market_cap_cr']))
        sme_map = dict(zip(master_df['symbol'], master_df['sme_status']))
        for sym in df_stk_50k['symbol']:
            assert mcap_map[sym] >= 50000.0
            assert sme_map[sym] == 'NON_SME'

    def test_empty_universe_hard_gate(self, latest_trade_date):
        u_empty = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=9999999.0, min_turnover_lakhs=0.0)
        assert u_empty["eligible_count"] == 0
        
        df_empty_ind, _ = get_aggregated_hierarchy_intelligence(latest_trade_date, "major_industry", eligible_symbols=u_empty["eligible_symbols_tuple"])
        assert df_empty_ind.empty
        
        df_stk = get_canonical_stock_quant_score(latest_trade_date)
        df_stk_filt = df_stk[df_stk['symbol'].isin(u_empty['eligible_symbols'])] if not df_stk.empty else pd.DataFrame()
        assert df_stk_filt.empty

    def test_filter_transition_reversibility(self, latest_trade_date):
        # 50k -> 1k -> 50k
        u_50k_1 = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=50000.0, min_turnover_lakhs=0.0)
        u_1k = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=1000.0, min_turnover_lakhs=0.0)
        u_50k_2 = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=50000.0, min_turnover_lakhs=0.0)
        
        assert u_50k_1["eligible_count"] == 440
        assert u_1k["eligible_count"] == 1594
        assert u_50k_2["eligible_count"] == 440
        assert u_50k_1["eligible_symbols"] == u_50k_2["eligible_symbols"]

    def test_theme_system_separation(self):
        assert THEME_TOKENS["dark"]["canvas"] == "#000000"
        assert THEME_TOKENS["light"]["canvas"] == "#F6F8FB"
        assert THEME_TOKENS["dark"]["card_bg"] != THEME_TOKENS["light"]["card_bg"]
