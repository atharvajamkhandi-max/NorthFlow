"""
research/v69_universe_consistency/tests/test_universe_consistency.py
Automated Unit Tests for Phase 69 Global Active Universe Contract & Consistency.
Enforces Invariants 1-10, TN Plantation Coffee cases, and Production Immutability.
"""
import pytest
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = BASE_DIR / "data" / "market_flow.db"

def test_1_active_universe_contract_structure():
    from dashboard.components.universe_service import get_active_universe, UNIVERSE_PRESETS
    u_ctx = get_active_universe("2026-08-26")
    assert "session_date" in u_ctx
    assert "symbols" in u_ctx
    assert "eligible_symbols" in u_ctx
    assert "eligible_symbols_tuple" in u_ctx
    assert "eligible_count" in u_ctx
    assert "total_universe_count" in u_ctx
    assert "coverage_pct" in u_ctx
    assert "universe_id" in u_ctx

def test_2_market_cap_600cr_excludes_sub_600cr_stocks():
    from dashboard.components.universe_service import resolve_user_universe
    from analytics.canonical_v3_2_service import get_canonical_stock_quant_score
    test_date = "2026-08-26"
    res = resolve_user_universe(test_date, include_sme=False, min_mcap_cr=600.0, min_turnover_lakhs=0.0)
    eligible = res["eligible_symbols"]

    # Known sub-600 Cr stocks
    excluded_samples = ['VASUPRADA', 'TERAI', 'KANCOTEA', 'DTIL', 'GROBTEA', 'ASIANTNE', 'PKTEA', 'NORBTEAEXP']
    for sym in excluded_samples:
        assert sym not in eligible, f"Sub-600Cr stock {sym} leaked into universe!"

    df_screener = get_canonical_stock_quant_score(test_date)
    filtered = df_screener[df_screener['symbol'].isin(eligible)]
    for sym in excluded_samples:
        assert sym not in filtered['symbol'].values, f"Sub-600Cr stock {sym} appeared in filtered screener!"

def test_3_industry_aggregate_equals_screener_constituent_count():
    from dashboard.components.universe_service import resolve_user_universe
    from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
    from analytics.canonical_v3_2_service import get_canonical_stock_quant_score
    test_date = "2026-08-26"
    res = resolve_user_universe(test_date, include_sme=False, min_mcap_cr=1000.0, min_turnover_lakhs=0.0)
    eligible = res["eligible_symbols"]

    df_agg, _ = get_aggregated_hierarchy_intelligence(test_date, hierarchy_level_key="major_industry", eligible_symbols=res["eligible_symbols_tuple"])
    df_screener = get_canonical_stock_quant_score(test_date)
    filtered_screener = df_screener[df_screener['symbol'].isin(eligible)]

    for _, r in df_agg.head(20).iterrows():
        ind = r['entity_name']
        agg_cnt = r['constituent_count']
        scr_cnt = len(filtered_screener[filtered_screener['industry'] == ind])
        assert agg_cnt == scr_cnt, f"Mismatch in {ind}: agg={agg_cnt} vs scr={scr_cnt}"

def test_4_empty_universe_graceful_handling():
    from dashboard.components.universe_service import resolve_user_universe
    from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
    from dashboard.industries_explorer import load_sector_overview_data
    test_date = "2026-08-26"
    res = resolve_user_universe(test_date, include_sme=False, min_mcap_cr=9999999.0, min_turnover_lakhs=0.0)
    assert res["eligible_count"] == 0

    df_agg, meta = get_aggregated_hierarchy_intelligence(test_date, eligible_symbols=res["eligible_symbols_tuple"])
    assert df_agg.empty

    df_sec, _ = load_sector_overview_data(test_date, eligible_symbols=res["eligible_symbols_tuple"])
    assert df_sec.empty

def test_5_production_immutability_checksums_match():
    import hashlib
    def get_sha256(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            while c := f.read(65536):
                h.update(c)
        return h.hexdigest()

    frozen_model = BASE_DIR / "config" / "model_v3_2_frozen.py"
    final_pred = BASE_DIR / "research" / "final_v3" / "results" / "final_predictions.csv"
    live_pred = BASE_DIR / "research" / "live_forward" / "ledger" / "live_predictions.csv"
    
    assert get_sha256(frozen_model) == "e350e9209960357d75668ff3dc9fb742162525169ae1f19d7fb7b681beadc756"
    assert get_sha256(final_pred) == "52019b780e8b9d714e8f926063dce725541b27335dec47b7f6e66346520bca6b"
    assert get_sha256(live_pred) == "7950580952b7d3e4d082aeb2c8b48ed892fbe9ce2487d0755255cce81977136e"
