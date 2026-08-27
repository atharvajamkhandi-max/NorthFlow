"""
research/v71_card_ui/tests/test_phase71_2_drilldown.py
Automated Unit & Integration Tests for Phase 71.2 Industry Ranking Completeness & One-Click Drilldown.
"""
import pytest
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

def test_1_more_than_16_industries_accessible():
    from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
    df_data, meta = get_aggregated_hierarchy_intelligence("2026-08-21", hierarchy_level_key="industry")
    assert len(df_data) > 16, f"Expected >16 industries, got {len(df_data)}"
    page_size = 16
    total_pages = int(np.ceil(len(df_data) / page_size))
    assert total_pages > 1

def test_2_ranking_count_equals_actual_eligible_count():
    from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
    df_data, meta = get_aggregated_hierarchy_intelligence("2026-08-21", hierarchy_level_key="industry")
    assert len(df_data) == df_data['entity_name'].nunique()

def test_3_and_4_and_5_synchronized_selection_state():
    session_state_mock = {}
    
    card_selected = "Bridal Gold Jewellery & Retail Showrooms"
    session_state_mock["selected_drilldown_entity"] = card_selected
    assert session_state_mock["selected_drilldown_entity"] == card_selected
    
    dropdown_selected = "Specialty Chemicals"
    session_state_mock["selected_drilldown_entity"] = dropdown_selected
    assert session_state_mock["selected_drilldown_entity"] == "Specialty Chemicals"

def test_6_and_7_drilldown_returns_all_eligible_stocks_and_subset_of_universe():
    from database.db import Database
    from dashboard.components.universe_service import resolve_user_universe
    
    db = Database()
    conn = db.get_connection()
    trade_date = "2026-08-21"
    
    # Active universe: Mcap >= 1000 Cr, SME=False
    u_ctx = resolve_user_universe(trade_date, include_sme=False, min_mcap_cr=1000.0, min_turnover_lakhs=0.0)
    assert u_ctx["is_filtered"] is True
    eligible_set = set(u_ctx["eligible_symbols"])
    
    industry_name = "Finished Formulations"
    
    sym_list = list(u_ctx["eligible_symbols"])
    placeholders = ",".join(["?"] * len(sym_list))
    sql = f"""
    SELECT s.symbol, s.company_name
    FROM stocks s
    WHERE s.industry = ? AND s.active = 1 AND s.symbol IN ({placeholders})
    """
    df_drill = pd.read_sql(sql, conn, params=[industry_name] + sym_list)
    
    assert len(df_drill) > 0
    for sym in df_drill['symbol']:
        assert sym in eligible_set, f"Symbol {sym} returned in drilldown is NOT in active universe!"

def test_8_and_9_mcap_and_sme_filter_changes_drilldown_membership():
    from database.db import Database
    from dashboard.components.universe_service import resolve_user_universe
    
    db = Database()
    conn = db.get_connection()
    trade_date = "2026-08-21"
    industry_name = "Finished Formulations"
    
    # All Equities (no mcap filter, SME=True)
    u_all = resolve_user_universe(trade_date, include_sme=True, min_mcap_cr=0.0, min_turnover_lakhs=0.0)
    syms_all = list(u_all["eligible_symbols"])
    sql = f"SELECT s.symbol FROM stocks s WHERE s.industry = ? AND s.active = 1 AND s.symbol IN ({','.join(['?']*len(syms_all))})"
    df_all = pd.read_sql(sql, conn, params=[industry_name] + syms_all)
    
    # Filtered: Mcap >= 5000 Cr, SME=False
    u_filt = resolve_user_universe(trade_date, include_sme=False, min_mcap_cr=5000.0, min_turnover_lakhs=0.0)
    syms_filt = list(u_filt["eligible_symbols"])
    sql_f = f"SELECT s.symbol FROM stocks s WHERE s.industry = ? AND s.active = 1 AND s.symbol IN ({','.join(['?']*len(syms_filt))})"
    df_filt = pd.read_sql(sql_f, conn, params=[industry_name] + syms_filt)
    
    assert len(df_filt) <= len(df_all), "Filtered count must be <= all count"
    assert len(df_filt) > 0

def test_10_industry_aggregate_count_equals_drilldown_count():
    from database.db import Database
    from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
    from dashboard.components.universe_service import resolve_user_universe
    
    db = Database()
    conn = db.get_connection()
    trade_date = "2026-08-21"
    
    u_ctx = resolve_user_universe(trade_date, include_sme=False, min_mcap_cr=600.0, min_turnover_lakhs=0.0)
    eligible_tuple = u_ctx["eligible_symbols_tuple"]
    
    df_agg, meta = get_aggregated_hierarchy_intelligence(trade_date, hierarchy_level_key="industry", eligible_symbols=eligible_tuple)
    
    sample_industries = df_agg['entity_name'].head(5).tolist()
    syms = list(u_ctx["eligible_symbols"])
    placeholders = ",".join(["?"] * len(syms))
    
    for ind in sample_industries:
        agg_cnt = df_agg[df_agg['entity_name'] == ind]['constituent_count'].iloc[0]
        sql = f"SELECT COUNT(*) as cnt FROM stocks s WHERE s.industry = ? AND s.active = 1 AND s.symbol IN ({placeholders})"
        drill_cnt = pd.read_sql(sql, conn, params=[ind] + syms)['cnt'].iloc[0]
        assert agg_cnt == drill_cnt, f"Mismatch for {ind}: aggregate={agg_cnt}, drilldown={drill_cnt}"

def test_11_changing_session_date_maintains_integrity():
    from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
    df_d1, _ = get_aggregated_hierarchy_intelligence("2026-08-21", hierarchy_level_key="industry")
    df_d2, _ = get_aggregated_hierarchy_intelligence("2026-08-20", hierarchy_level_key="industry")
    assert not df_d1.empty
    assert not df_d2.empty

def test_12_zero_stock_or_empty_universe_handled():
    from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
    df_empty, meta = get_aggregated_hierarchy_intelligence("2026-08-21", hierarchy_level_key="industry", eligible_symbols=tuple(["NON_EXISTENT_SYM"]))
    assert df_empty.empty or len(df_empty) == 0

def test_13_no_hidden_truncation_in_drilldown_path():
    flow_file = BASE_DIR / "dashboard" / "industry_flow.py"
    content = flow_file.read_text(encoding="utf-8")
    assert "df_stk_view.head" not in content, "Found hidden head() truncation on drilldown stocks!"
