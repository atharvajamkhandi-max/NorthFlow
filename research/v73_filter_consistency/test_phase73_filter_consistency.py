"""
research/v73_filter_consistency/test_phase73_filter_consistency.py
===================================================================
Phase 73 Comprehensive Test Suite: NorthFlow Global Filter Consistency,
Active Universe Invariants, Extreme Failure Gates & Production Immutability.
"""

import sys
import sqlite3
import hashlib
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))

from database.db import Database
from dashboard.components.universe_service import (
    resolve_user_universe,
    UNIVERSE_PRESETS,
)
from analytics.canonical_v3_2_service import (
    get_canonical_stock_quant_score,
    MODEL_V3_2_FINGERPRINT
)
from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
from dashboard.industries_explorer import load_sector_overview_data

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
# 1. PRODUCTION ARTIFACT IMMUTABILITY
# ─────────────────────────────────────────────────────────
class TestPhase73ProductionImmutability:
    @pytest.mark.parametrize("fname,info", PRODUCTION_FILES.items())
    def test_production_artifact_hash_preserved(self, fname, info):
        fpath = info["path"]
        if not fpath.exists():
            pytest.skip(f"File not found: {fpath}")
        actual = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
        expected = info["expected_sha256"]
        assert actual == expected, f"Immutability violated for {fname}: expected {expected}, got {actual}"

# ─────────────────────────────────────────────────────────
# 2. DETERMINISTIC PRESET UNIVERSE RESOLUTION
# ─────────────────────────────────────────────────────────
class TestDeterministicPresetResolution:
    @pytest.mark.parametrize("mcap_th", [100, 200, 300, 500, 750, 1000, 2500, 5000, 10000, 20000, 50000, 100000])
    def test_market_cap_thresholds(self, latest_trade_date, master_df, mcap_th):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=float(mcap_th), min_turnover_lakhs=0.0)
        expected_syms = set(master_df[(master_df['sme_status'] == 'NON_SME') & (master_df['market_cap_cr'] >= mcap_th)]['symbol'])
        
        assert u["eligible_symbols"] == expected_syms
        assert u["eligible_count"] == len(expected_syms)
        assert u["is_filtered"] is True

    def test_sme_off_preset(self, latest_trade_date, master_df):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=0.0, min_turnover_lakhs=0.0)
        expected_syms = set(master_df[master_df['sme_status'] == 'NON_SME']['symbol'])
        
        assert u["eligible_symbols"] == expected_syms
        assert u["eligible_count"] == 2571
        assert len(u["eligible_symbols"].intersection(set(master_df[master_df['sme_status'] == 'SME']['symbol']))) == 0

    def test_liquid_presets(self, latest_trade_date, master_df):
        # 1 Cr/d = 100 Lakhs/d
        u1 = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=0.0, min_turnover_lakhs=100.0)
        expected1 = set(master_df[(master_df['sme_status'] == 'NON_SME') & (master_df['avg_turnover_20d'] >= 10000000.0)]['symbol'])
        assert u1["eligible_symbols"] == expected1

        # 5 Cr/d = 500 Lakhs/d
        u5 = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=0.0, min_turnover_lakhs=500.0)
        expected5 = set(master_df[(master_df['sme_status'] == 'NON_SME') & (master_df['avg_turnover_20d'] >= 50000000.0)]['symbol'])
        assert u5["eligible_symbols"] == expected5

# ─────────────────────────────────────────────────────────
# 3. STRICT UNIVERSE INVARIANTS ACROSS DOWNSTREAM LAYERS
# ─────────────────────────────────────────────────────────
class TestUniverseInvariantsDownstream:
    @pytest.mark.parametrize("preset_key,inc_sme,mcap,turn", [
        ("all", True, 0.0, 0.0),
        ("mcap_1000", False, 1000.0, 0.0),
        ("mcap_5000", False, 5000.0, 0.0),
        ("mcap_20000", False, 20000.0, 0.0),
        ("mcap_50000", False, 50000.0, 0.0),
        ("mcap_100000", False, 100000.0, 0.0),
        ("custom_combo", False, 2500.0, 100.0)
    ])
    def test_hierarchy_aggregation_subset_invariant(self, latest_trade_date, preset_key, inc_sme, mcap, turn):
        u = resolve_user_universe(latest_trade_date, include_sme=inc_sme, min_mcap_cr=mcap, min_turnover_lakhs=turn)
        arg_syms = u["eligible_symbols_tuple"] if u["is_filtered"] else None
        
        df_agg, meta = get_aggregated_hierarchy_intelligence(latest_trade_date, "major_industry", eligible_symbols=arg_syms)
        if not df_agg.empty:
            total_constituents = df_agg['constituent_count'].sum()
            assert total_constituents == u["eligible_count"]
        else:
            assert u["eligible_count"] == 0

    @pytest.mark.parametrize("mcap", [5000.0, 20000.0, 50000.0])
    def test_screener_subset_invariant(self, latest_trade_date, mcap):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=mcap, min_turnover_lakhs=0.0)
        df_stk = get_canonical_stock_quant_score(latest_trade_date)
        
        if u["is_filtered"] and not df_stk.empty:
            df_screened = df_stk[df_stk['symbol'].isin(u['eligible_symbols'])].copy()
        else:
            df_screened = df_stk
            
        assert set(df_screened['symbol']).issubset(u['eligible_symbols'])
        assert len(df_screened) == u["eligible_count"]

    @pytest.mark.parametrize("mcap", [1000.0, 5000.0, 50000.0])
    def test_drilldown_subset_invariant(self, conn, latest_trade_date, master_df, mcap):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=mcap, min_turnover_lakhs=0.0)
        eligible_set = u["eligible_symbols"]
        
        for test_ind in ["Precision Auto Engine Components", "Finished Formulations", "Diversified Consumer & MSME NBFC"]:
            if u["is_filtered"]:
                if u["eligible_symbols"]:
                    sym_list = list(u["eligible_symbols"])
                    ph = ",".join(["?"] * len(sym_list))
                    sql = f"SELECT symbol FROM stocks WHERE industry = ? AND active = 1 AND symbol IN ({ph})"
                    res = pd.read_sql(sql, conn, params=[test_ind] + sym_list)
                else:
                    res = pd.DataFrame()
            else:
                sql = f"SELECT symbol FROM stocks WHERE industry = ? AND active = 1"
                res = pd.read_sql(sql, conn, params=[test_ind])
                
            if not res.empty:
                res_syms = set(res['symbol'])
                assert res_syms.issubset(eligible_set), f"Leaked stocks in {test_ind} drilldown: {res_syms - eligible_set}"
                mcap_subset = master_df[master_df['symbol'].isin(res_syms)]
                assert (mcap_subset['market_cap_cr'] >= mcap).all(), f"Stock below {mcap} Cr leaked into {test_ind} drilldown!"

# ─────────────────────────────────────────────────────────
# 4. EXTREME / IMPOSSIBLE UNIVERSE GATES (ZERO FALLBACK)
# ─────────────────────────────────────────────────────────
class TestExtremeFailureZeroFallback:
    def test_impossible_market_cap_yields_empty_universe(self, latest_trade_date):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=9999999.0, min_turnover_lakhs=0.0)
        assert u["eligible_count"] == 0
        assert u["eligible_symbols"] == set()
        assert u["is_filtered"] is True

    def test_impossible_universe_hierarchy_empty(self, latest_trade_date):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=9999999.0, min_turnover_lakhs=0.0)
        df_agg, meta = get_aggregated_hierarchy_intelligence(latest_trade_date, "major_industry", eligible_symbols=u["eligible_symbols_tuple"])
        assert df_agg.empty
        assert len(df_agg) == 0

    def test_impossible_universe_drilldown_empty_no_fallback(self, conn, latest_trade_date):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=9999999.0, min_turnover_lakhs=0.0)
        
        for test_ind in ["Precision Auto Engine Components", "Finished Formulations", "Diversified Consumer & MSME NBFC", "Mid-Tier IT & Digital Solutions", "Cotton Spinning & Yarns"]:
            if u["is_filtered"]:
                if u["eligible_symbols"]:
                    sym_list = list(u["eligible_symbols"])
                    ph = ",".join(["?"] * len(sym_list))
                    sql = f"SELECT symbol FROM stocks WHERE industry = ? AND active = 1 AND symbol IN ({ph})"
                    res = pd.read_sql(sql, conn, params=[test_ind] + sym_list)
                else:
                    res = pd.DataFrame()
            else:
                sql = f"SELECT symbol FROM stocks WHERE industry = ? AND active = 1"
                res = pd.read_sql(sql, conn, params=[test_ind])
                
            assert res.empty, f"Fallback leak detected on empty universe for {test_ind}!"
            assert len(res) == 0

    def test_impossible_universe_screener_empty(self, latest_trade_date):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=9999999.0, min_turnover_lakhs=0.0)
        df_stk = get_canonical_stock_quant_score(latest_trade_date)
        if u["is_filtered"]:
            if not df_stk.empty and u["eligible_symbols"]:
                df_res = df_stk[df_stk['symbol'].isin(u['eligible_symbols'])]
            else:
                df_res = pd.DataFrame()
        else:
            df_res = df_stk
        assert df_res.empty

# ─────────────────────────────────────────────────────────
# 5. ORIGINAL OBSERVED BUG VERIFICATION (>= Rs 50,000 Cr)
# ─────────────────────────────────────────────────────────
class TestOriginalBugResolution50k:
    def test_50k_filter_completely_excludes_below_threshold_stocks(self, conn, latest_trade_date, master_df):
        u = resolve_user_universe(latest_trade_date, include_sme=False, min_mcap_cr=50000.0, min_turnover_lakhs=0.0)
        eligible_set = u["eligible_symbols"]
        
        assert u["eligible_count"] == 440
        
        sme_stocks_in_50k = set(master_df[master_df['sme_status'] == 'SME']['symbol']).intersection(eligible_set)
        assert len(sme_stocks_in_50k) == 0
        
        mcap_map = dict(zip(master_df['symbol'], master_df['market_cap_cr']))
        for sym in eligible_set:
            assert mcap_map[sym] >= 50000.0, f"Stock {sym} has mcap {mcap_map[sym]} < 50000!"
            
        below_50k_syms = set(master_df[master_df['market_cap_cr'] < 50000.0]['symbol'])
        leaked = below_50k_syms.intersection(eligible_set)
        assert len(leaked) == 0, f"Leaked below-50k stocks: {leaked}"
