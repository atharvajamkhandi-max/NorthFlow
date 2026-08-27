"""
research/v66_universe/tests/test_universe_and_navigation.py
Isolated unit tests for Phase 66 Terminal Navigation & User-Controlled Market Universe.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = BASE_DIR / "data" / "market_flow.db"

def test_1_universe_resolution_all_equities():
    from dashboard.components.universe_service import resolve_user_universe
    res = resolve_user_universe("2026-08-26", include_sme=True, min_mcap_cr=0.0, min_turnover_lakhs=0.0)
    assert res["eligible_count"] > 2500
    assert res["total_universe_count"] > 2500
    assert res["coverage_pct"] == 100.0
    assert not res["is_filtered"]

def test_2_universe_resolution_sme_exclusion():
    from dashboard.components.universe_service import resolve_user_universe
    res_all = resolve_user_universe("2026-08-26", include_sme=True, min_mcap_cr=0.0, min_turnover_lakhs=0.0)
    res_no_sme = resolve_user_universe("2026-08-26", include_sme=False, min_mcap_cr=0.0, min_turnover_lakhs=0.0)
    assert res_no_sme["eligible_count"] < res_all["eligible_count"]
    assert res_no_sme["is_filtered"]
    assert res_no_sme["sme_count"] > 0

def test_3_universe_resolution_mcap_filtering():
    from dashboard.components.universe_service import resolve_user_universe
    res_1k = resolve_user_universe("2026-08-26", include_sme=False, min_mcap_cr=1000.0, min_turnover_lakhs=0.0)
    res_5k = resolve_user_universe("2026-08-26", include_sme=False, min_mcap_cr=5000.0, min_turnover_lakhs=0.0)
    assert res_5k["eligible_count"] < res_1k["eligible_count"]
    assert res_1k["eligible_count"] > 1000

def test_4_hierarchy_aggregation_with_universe_filtering():
    from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
    from dashboard.components.universe_service import resolve_user_universe
    res = resolve_user_universe("2026-08-26", include_sme=False, min_mcap_cr=5000.0, min_turnover_lakhs=0.0)
    df_filtered, _ = get_aggregated_hierarchy_intelligence("2026-08-26", "major_industry", eligible_symbols=res["eligible_symbols_tuple"])
    df_all, _ = get_aggregated_hierarchy_intelligence("2026-08-26", "major_industry")
    assert not df_filtered.empty
    assert not df_all.empty
    assert df_filtered['constituent_count'].sum() < df_all['constituent_count'].sum()

def test_5_production_immutability_checksums_match():
    pre_file = BASE_DIR / "research" / "v66_universe" / "safety" / "checksums_preflight.json"
    post_file = BASE_DIR / "research" / "v66_universe" / "safety" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
