"""
research/v70_market_cap/tests/test_phase70_market_cap.py
Automated Unit Tests for Phase 70 Market-Cap Data Quality & Point-in-Time Universe Accuracy.
"""
import pytest
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = BASE_DIR / "data" / "market_flow.db"

def test_1_market_cap_service_contract_and_quality_provenance():
    from analytics.market_cap_service import get_market_cap_service, QualityStatus, SourceTier
    svc = get_market_cap_service()
    test_date = "2026-08-26"

    # Single symbol query
    mcap_rel = svc.get_market_cap("RELIANCE", test_date)
    assert mcap_rel is not None and mcap_rel > 100000.0

    # Multi-symbol query
    mcaps = svc.get_market_caps(["RELIANCE", "TCS", "INFY"], test_date)
    assert len(mcaps) == 3
    assert all(v > 10000.0 for v in mcaps.values())

    # Single symbol provenance
    prov = svc.get_market_cap_provenance("RELIANCE", test_date)
    assert prov["symbol"] == "RELIANCE"
    assert prov["quality_status"] == QualityStatus.VERIFIED
    assert prov["source_tier"] == SourceTier.TIER_3
    assert prov["market_cap_cr"] > 1000000.0
    assert "historical_reconstruction_note" in prov

    # Summary provenance
    summary = svc.get_market_cap_provenance_summary(test_date)
    assert summary["total_securities"] == 3028
    assert summary["coverage_pct"] == 100.0
    assert summary["verified_pct"] >= 95.0
    assert QualityStatus.VERIFIED in summary["quality_distribution"]
    assert "historical_reconstruction_note" in summary

def test_2_expanded_universe_presets_and_monotonicity():
    from dashboard.components.universe_service import UNIVERSE_PRESETS, resolve_user_universe
    test_date = "2026-08-26"

    # Verify all requested presets are present
    required_presets = [
        "all", "no_sme", "mcap_100", "mcap_200", "mcap_300", "mcap_500",
        "mcap_750", "mcap_1000", "mcap_2500", "mcap_5000", "mcap_10000",
        "mcap_20000", "mcap_50000", "liquid_1cr", "liquid_5cr", "custom"
    ]
    for p in required_presets:
        assert p in UNIVERSE_PRESETS, f"Preset {p} missing from UNIVERSE_PRESETS"

    # Verify strict monotonic decrease as market cap floor rises
    mcap_sequence = [0.0, 100.0, 200.0, 300.0, 500.0, 750.0, 1000.0, 2500.0, 5000.0, 10000.0, 20000.0, 50000.0]
    prev_count = 999999
    for mcap in mcap_sequence:
        res = resolve_user_universe(test_date, include_sme=False, min_mcap_cr=mcap, min_turnover_lakhs=0.0)
        cnt = res["eligible_count"]
        assert cnt <= prev_count, f"Monotonicity violation at Mcap >= {mcap}: {cnt} > {prev_count}"
        prev_count = cnt

def test_3_sme_and_liquidity_composition():
    from dashboard.components.universe_service import resolve_user_universe
    test_date = "2026-08-26"

    # Baseline (no SME, >= 1000 Cr, >= 100 L turnover)
    res_comp = resolve_user_universe(test_date, include_sme=False, min_mcap_cr=1000.0, min_turnover_lakhs=100.0)
    elig_comp = res_comp["eligible_symbols"]

    # Verify composition is a subset of mcap-only and liquidity-only
    res_mcap = resolve_user_universe(test_date, include_sme=False, min_mcap_cr=1000.0, min_turnover_lakhs=0.0)
    res_liq = resolve_user_universe(test_date, include_sme=False, min_mcap_cr=0.0, min_turnover_lakhs=100.0)

    assert elig_comp.issubset(res_mcap["eligible_symbols"])
    assert elig_comp.issubset(res_liq["eligible_symbols"])
    assert len(elig_comp) <= len(res_mcap["eligible_symbols"])
    assert len(elig_comp) <= len(res_liq["eligible_symbols"])

def test_4_tn_plantation_coffee_exact_progression():
    from database.db import Database
    from dashboard.components.universe_service import resolve_user_universe
    from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
    from analytics.canonical_v3_2_service import get_canonical_stock_quant_score

    db = Database()
    test_date = "2026-08-26"
    df_scr = get_canonical_stock_quant_score(test_date)

    thresholds = [
        (True, 0.0),
        (False, 0.0),
        (False, 600.0),
        (False, 1000.0),
        (False, 5000.0),
        (False, 20000.0)
    ]

    for inc_sme, mcap_floor in thresholds:
        res = resolve_user_universe(test_date, include_sme=inc_sme, min_mcap_cr=mcap_floor, min_turnover_lakhs=0.0)
        elig = res["eligible_symbols"]
        elig_tup = res["eligible_symbols_tuple"]

        # Aggregate count
        df_agg, _ = get_aggregated_hierarchy_intelligence(test_date, hierarchy_level_key="major_industry", eligible_symbols=elig_tup)
        
        for ind in ['Tea Plantations & Packaging', 'Tea & Coffee Plantations']:
            row_ind = df_agg[df_agg['entity_name'] == ind]
            agg_cnt = row_ind['constituent_count'].iloc[0] if not row_ind.empty else 0

            # Screener count
            filt_scr = df_scr[df_scr['symbol'].isin(elig)] if res["is_filtered"] else df_scr
            scr_cnt = len(filt_scr[filt_scr['industry'] == ind])

            # Detail table count
            df_const = db.get_stocks_by_industry(ind, trade_date=test_date)
            const_cnt = len(df_const[df_const['symbol'].isin(elig)]) if res["is_filtered"] else len(df_const)

            assert agg_cnt == scr_cnt == const_cnt, f"Mismatch in {ind} at mcap={mcap_floor}, sme={inc_sme}: agg={agg_cnt}, scr={scr_cnt}, const={const_cnt}"

def test_5_extreme_zero_universe_graceful_handling():
    from dashboard.components.universe_service import resolve_user_universe
    from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
    from dashboard.industries_explorer import load_sector_overview_data
    from analytics.canonical_v3_2_service import get_canonical_stock_quant_score

    test_date = "2026-08-26"
    res = resolve_user_universe(test_date, include_sme=False, min_mcap_cr=9999999.0, min_turnover_lakhs=0.0)
    assert res["eligible_count"] == 0
    assert len(res["eligible_symbols"]) == 0

    df_agg, meta = get_aggregated_hierarchy_intelligence(test_date, eligible_symbols=res["eligible_symbols_tuple"])
    assert df_agg.empty

    df_sec, df_raw = load_sector_overview_data(test_date, eligible_symbols=res["eligible_symbols_tuple"])
    assert df_sec.empty
    assert df_raw.empty

    df_scr = get_canonical_stock_quant_score(test_date)
    filt_scr = df_scr[df_scr['symbol'].isin(res["eligible_symbols"])]
    assert filt_scr.empty

def test_6_cross_sectional_score_dependency():
    from dashboard.components.universe_service import resolve_user_universe
    from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
    test_date = "2026-08-26"

    # Universal
    res_all = resolve_user_universe(test_date, include_sme=True, min_mcap_cr=0.0, min_turnover_lakhs=0.0)
    df_all, _ = get_aggregated_hierarchy_intelligence(test_date, hierarchy_level_key="major_industry", eligible_symbols=res_all["eligible_symbols_tuple"])

    # Filtered >= 5000 Cr
    res_5k = resolve_user_universe(test_date, include_sme=False, min_mcap_cr=5000.0, min_turnover_lakhs=0.0)
    df_5k, _ = get_aggregated_hierarchy_intelligence(test_date, hierarchy_level_key="major_industry", eligible_symbols=res_5k["eligible_symbols_tuple"])

    # Verified that at least some industry constituent counts and scores differ
    assert len(df_5k) < len(df_all)
    row_tea_all = df_all[df_all['entity_name'] == 'Tea Plantations & Packaging']
    row_tea_5k = df_5k[df_5k['entity_name'] == 'Tea Plantations & Packaging']
    assert row_tea_all['constituent_count'].iloc[0] != row_tea_5k['constituent_count'].iloc[0]

def test_7_production_immutability_checksums():
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
    live_hashes = BASE_DIR / "research" / "live_forward" / "ledger" / "live_hashes.csv"
    promotion_status = BASE_DIR / "research" / "live_forward" / "promotion_gate" / "promotion_status.json"
    
    assert get_sha256(frozen_model) == "e350e9209960357d75668ff3dc9fb742162525169ae1f19d7fb7b681beadc756"
    assert get_sha256(final_pred) == "52019b780e8b9d714e8f926063dce725541b27335dec47b7f6e66346520bca6b"
    assert get_sha256(live_pred) == "7950580952b7d3e4d082aeb2c8b48ed892fbe9ce2487d0755255cce81977136e"
    assert get_sha256(live_hashes) == "0010c55813170804e62726ce458ac78cee0394b8995b9f3d2bd8066014c0ca43"
    assert get_sha256(promotion_status) == "e9761f0b27853f1e2d3635dbe11a36a859b2dee899a1aeb6a15a8f39c1575fa3"
