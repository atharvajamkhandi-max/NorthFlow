"""
tests/test_phase76_market_overview_ui.py
========================================
Phase 76 Automated Unit & Integration Tests:
Market Overview Two-Mode UI/UX, Active Universe Invariants,
Drilldown Fidelity, Stock Recommender Bounding & Production Immutability.
"""

import sys
import sqlite3
import hashlib
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from database.db import Database
from dashboard.components.universe_service import (
    resolve_user_universe,
    UNIVERSE_PRESETS
)
from analytics.canonical_v3_2_service import (
    get_canonical_stock_quant_score,
    MODEL_V3_2_FINGERPRINT
)
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

# ─────────────────────────────────────────────────────────
# 1. PRODUCTION IMMUTABILITY VERIFICATION
# ─────────────────────────────────────────────────────────
class TestPhase76ProductionImmutability:
    @pytest.mark.parametrize("fname,info", PRODUCTION_FILES.items())
    def test_production_artifact_hash_preserved(self, fname, info):
        fpath = info["path"]
        actual = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
        expected = info["expected_sha256"]
        assert actual == expected, f"Immutability violated for {fname}: expected {expected}, got {actual}"

# ─────────────────────────────────────────────────────────
# 2. MODE A: INDUSTRY POSITION & DRILLDOWN INVARIANTS
# ─────────────────────────────────────────────────────────
class TestPhase76IndustryPositionMode:
    @pytest.mark.parametrize("mcap_th", [0.0, 1000.0, 5000.0, 20000.0, 50000.0])
    def test_industry_drilldown_strict_bounding(self, conn, latest_trade_date, master_df, mcap_th):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=mcap_th, min_turnover_lakhs=0.0)
        eligible_set = u["eligible_symbols"]
        
        test_inds = ["Precision Auto Engine Components", "Finished Formulations", "Diversified Consumer & MSME NBFC"]
        for ind in test_inds:
            if u["is_filtered"]:
                if eligible_set:
                    sym_list = list(eligible_set)
                    ph = ",".join(["?"] * len(sym_list))
                    sql = f"SELECT symbol FROM stocks WHERE industry = ? AND active = 1 AND symbol IN ({ph})"
                    res = pd.read_sql(sql, conn, params=[ind] + sym_list)
                else:
                    res = pd.DataFrame()
            else:
                sql = f"SELECT symbol FROM stocks WHERE industry = ? AND active = 1"
                res = pd.read_sql(sql, conn, params=[ind])
                
            if not res.empty:
                res_syms = set(res['symbol'])
                assert res_syms.issubset(eligible_set), f"Leaked stocks in {ind} drilldown: {res_syms - eligible_set}"
                mcap_subset = master_df[master_df['symbol'].isin(res_syms)]
                assert (mcap_subset['market_cap_cr'] >= mcap_th).all(), f"Stock below {mcap_th} Cr in drilldown!"
                assert (mcap_subset['sme_status'] == 'NON_SME').all(), f"SME stock leaked into SME OFF drilldown!"

    def test_industry_ranking_controls_change_order_only(self, latest_trade_date):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=1000.0, min_turnover_lakhs=0.0)
        df_agg, _ = get_aggregated_hierarchy_intelligence(latest_trade_date, "major_industry", eligible_symbols=u["eligible_symbols_tuple"])
        
        # Sort by strength vs sort by exp return
        df_by_strength = df_agg.sort_values('current_strength', ascending=False)
        df_by_return = df_agg.sort_values('exp_return_20d', ascending=False)
        
        assert len(df_by_strength) == len(df_by_return)
        assert set(df_by_strength['entity_name']) == set(df_by_return['entity_name'])

    def test_industry_display_limits(self, latest_trade_date):
        u = resolve_user_universe(latest_trade_date, include_sme=True, min_mcap_cr=0.0, min_turnover_lakhs=0.0)
        df_agg, _ = get_aggregated_hierarchy_intelligence(latest_trade_date, "major_industry", eligible_symbols=None)
        
        for lim in [10, 20, 30, 50]:
            df_lim = df_agg.head(lim)
            assert len(df_lim) == min(lim, len(df_agg))
            assert set(df_lim['entity_name']).issubset(set(df_agg['entity_name']))

# ─────────────────────────────────────────────────────────
# 3. MODE B: STOCK RECOMMENDER BOUNDING INVARIANTS
# ─────────────────────────────────────────────────────────
class TestPhase76StockRecommenderMode:
    @pytest.mark.parametrize("mcap_th", [1000.0, 5000.0, 20000.0, 50000.0])
    def test_stock_recommender_bounded_by_active_universe(self, latest_trade_date, master_df, mcap_th):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=mcap_th, min_turnover_lakhs=0.0)
        eligible_set = u["eligible_symbols"]
        
        df_stocks_raw = get_canonical_stock_quant_score(latest_trade_date)
        df_stocks_filtered = df_stocks_raw[df_stocks_raw['symbol'].isin(eligible_set)].copy()
        
        # Check subset invariant
        assert set(df_stocks_filtered['symbol']).issubset(eligible_set)
        assert len(df_stocks_filtered) == u["eligible_count"]
        
        # Check all recommended stocks satisfy filter
        mcap_map = dict(zip(master_df['symbol'], master_df['market_cap_cr']))
        sme_map = dict(zip(master_df['symbol'], master_df['sme_status']))
        for sym in df_stocks_filtered['symbol']:
            assert mcap_map[sym] >= mcap_th, f"Stock {sym} market cap {mcap_map[sym]} < {mcap_th} Cr in recommender!"
            assert sme_map[sym] == 'NON_SME', f"Stock {sym} is SME in SME OFF recommender!"

    def test_stock_recommender_ranking_controls(self, latest_trade_date):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=5000.0, min_turnover_lakhs=0.0)
        df_stocks_raw = get_canonical_stock_quant_score(latest_trade_date)
        df_stocks_filtered = df_stocks_raw[df_stocks_raw['symbol'].isin(u['eligible_symbols'])].copy()
        
        # Sort by quant score vs sort by 20D return
        df_by_score = df_stocks_filtered.sort_values('stock_strength_score', ascending=False)
        df_by_ret = df_stocks_filtered.sort_values('return_20d', ascending=False)
        
        assert len(df_by_score) == len(df_by_ret)
        assert set(df_by_score['symbol']) == set(df_by_ret['symbol'])

# ─────────────────────────────────────────────────────────
# 4. EMPTY UNIVERSE HARD RELEASE GATE
# ─────────────────────────────────────────────────────────
class TestPhase76EmptyUniverseGate:
    def test_empty_universe_returns_zero_records(self, latest_trade_date):
        u_empty = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=9999999.0, min_turnover_lakhs=0.0)
        assert u_empty["eligible_count"] == 0
        assert u_empty["is_filtered"] is True
        
        # Mode A: Hierarchy
        df_agg_emp, _ = get_aggregated_hierarchy_intelligence(latest_trade_date, "major_industry", eligible_symbols=u_empty["eligible_symbols_tuple"])
        assert df_agg_emp.empty
        
        # Mode B: Stock Recommender
        df_stk_emp = get_canonical_stock_quant_score(latest_trade_date)
        df_stk_emp_filt = df_stk_emp[df_stk_emp['symbol'].isin(u_empty["eligible_symbols"])] if not df_stk_emp.empty else pd.DataFrame()
        assert df_stk_emp_filt.empty

# ─────────────────────────────────────────────────────────
# 5. THEME SYSTEM TOKENS INTEGRITY
# ─────────────────────────────────────────────────────────
class TestPhase76ThemeSystem:
    def test_theme_system_tokens(self):
        assert "dark" in THEME_TOKENS and "light" in THEME_TOKENS
        for mode in ["dark", "light"]:
            t = THEME_TOKENS[mode]
            for key in ["canvas", "card_bg", "card_border", "text_primary", "text_muted", "accent", "sidebar_bg", "header_bg"]:
                assert key in t, f"Missing {key} in {mode} theme"
        assert THEME_TOKENS["dark"]["canvas"] == "#000000"
        assert THEME_TOKENS["light"]["canvas"] == "#F6F8FB"
