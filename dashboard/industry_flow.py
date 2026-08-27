"""
Industry Flow Screener Page: Complete Cross-Sectional Ranking with 1-Click Stock Drilldown.
Phase 71.2: Full Ranking Completeness, Synchronized One-Click Drilldown & Universe Integrity.
"""

import streamlit as st
import pandas as pd
import numpy as np
import textwrap
from database.db import Database
from dashboard.components.topbar import render_topbar
from dashboard.components.global_state import get_hierarchy_metadata, render_hierarchy_badge_inline
from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
from dashboard.components.analytical_card import render_analytical_card_grid
from dashboard.components.theme import get_theme_tokens, get_theme_mode

def render_industry_flow(db: Database, selected_date: str):
    t = get_theme_tokens()
    meta = get_hierarchy_metadata()
    level_label = meta["label"]
    level_plural = meta["plural"]
    level_col = meta["col"]
    badge_html = render_hierarchy_badge_inline()

    render_topbar(selected_date, page_title=f"{level_label} Money Flow Screener")

    # Authoritative Active Universe Contract
    from dashboard.components.universe_service import get_current_universe_context, render_universe_status_chip
    u_ctx = get_current_universe_context(selected_date)
    render_universe_status_chip(u_ctx)

    eligible_syms = u_ctx["eligible_symbols_tuple"] if u_ctx["is_filtered"] else None
    df_data, market_meta = get_aggregated_hierarchy_intelligence(selected_date, hierarchy_level_key=None, eligible_symbols=eligible_syms)
    if df_data.empty:
        st.warning(f"No metric data found for active market universe on session {selected_date}.")
        return

    # Filter Controls Bar
    f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([1.4, 1.5, 1.2, 1.5, 1.0])
    with f_c1:
        if level_col != "macro_sector":
            sec_opts = ["All Macro Sectors"] + sorted(df_data['macro_sector'].dropna().unique().tolist())
            sel_sec = st.selectbox("1. Parent Sector", sec_opts, index=0, key="flow_sec_filter")
        else:
            sel_sec = "All Macro Sectors"
            st.selectbox("1. Category", ["All Sectors (Domain View)"], index=0, disabled=True, key="flow_sec_filter")
    
    with f_c2:
        min_constituents = st.slider(
            "2. Min Constituents",
            min_value=1,
            max_value=50,
            value=5,
            step=1,
            help="Controls the minimum number of constituent stocks required for an industry to appear.",
            key="flow_min_constituents"
        )
    
    with f_c3:
        sel_action = st.selectbox("3. Action", ["All Actions", "STRONG BUY", "BUY", "WATCH", "NEUTRAL", "REDUCE", "AVOID"], index=0, key="flow_action_filter")
    
    with f_c4:
        search_query = st.text_input("4. Search Name", placeholder=f"Type {level_label.lower()} name...", key="flow_search_v3")

    with f_c5:
        flow_view_mode = st.radio("View", ["🗂️ Cards", "📊 Table"], horizontal=True, key="flow_view_mode_select", label_visibility="collapsed")

    # 1. Apply Minimum Constituents Breadth Filter
    filtered = df_data[df_data['constituent_count'] >= min_constituents].copy()
    eligible_after_breadth = len(filtered)

    # 2. Apply Sector Filter
    if sel_sec != "All Macro Sectors" and level_col != "macro_sector":
        filtered = filtered[filtered['macro_sector'] == sel_sec]

    # 3. Apply Action Filter
    if sel_action != "All Actions":
        filtered = filtered[filtered['final_action'] == sel_action]

    # 4. Apply Search Query
    if search_query.strip():
        q_clean = search_query.strip().lower()
        filtered = filtered[
            filtered['entity_name'].str.lower().str.contains(q_clean) |
            filtered['macro_sector'].str.lower().str.contains(q_clean)
        ]

    filtered = filtered.sort_values('current_strength', ascending=False).reset_index(drop=True)
    filtered['Rank'] = np.arange(1, len(filtered) + 1)
    filtered['breadth_qualification'] = np.where(filtered['constituent_count'] >= 5, 'PRIMARY', 'RESEARCH ONLY')

    total_filtered = len(filtered)

    # Maintain single authoritative selected industry in session_state
    drill_options = filtered['entity_name'].tolist() if not filtered.empty else []
    
    if "selected_drilldown_entity" not in st.session_state or st.session_state["selected_drilldown_entity"] not in drill_options:
        if drill_options:
            st.session_state["selected_drilldown_entity"] = drill_options[0]
        else:
            st.session_state["selected_drilldown_entity"] = None
            
    active_selected_entity = st.session_state.get("selected_drilldown_entity", None)

    # Pagination & Ranking Header
    p_c1, p_c2 = st.columns([2.5, 1.5])
    with p_c1:
        bar_html = f"""<div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 4px 0;">
<span style="font-size: 0.88rem; font-weight: 700; color: {t['text_primary']};">
Showing <b style="color: {t['accent']};">{total_filtered}</b> eligible {level_plural.lower()} (out of {eligible_after_breadth} breadth-qualified)
</span>
<span style="font-size: 0.70rem; color: {t['accent']}; background: {t['accent_muted']}; padding: 2px 8px; border-radius: 4px; border: 1px solid {t['card_border']}; font-weight: 700; font-family: 'JetBrains Mono';">
N ≥ {min_constituents}
</span>
<div>{badge_html}</div>
</div>"""
        st.markdown(textwrap.dedent(bar_html).strip(), unsafe_allow_html=True)
        
    with p_c2:
        page_size_opt = st.selectbox(
            "Cards per page",
            options=["16 per page", "32 per page", "64 per page", "Show All"],
            index=0,
            key="flow_page_size_sel",
            label_visibility="collapsed"
        )

    if filtered.empty:
        st.info(f"No {level_plural.lower()} match the selected criteria (Min Constituents = {min_constituents}). Try lowering the slider.")
        return

    # Determine pagination slice
    if page_size_opt == "16 per page":
        page_limit = 16
    elif page_size_opt == "32 per page":
        page_limit = 32
    elif page_size_opt == "64 per page":
        page_limit = 64
    else:
        page_limit = total_filtered

    total_pages = max(1, int(np.ceil(total_filtered / page_limit)))
    if "flow_page_num" not in st.session_state:
        st.session_state["flow_page_num"] = 1
    if st.session_state["flow_page_num"] > total_pages:
        st.session_state["flow_page_num"] = 1

    curr_page = st.session_state["flow_page_num"]
    start_idx = (curr_page - 1) * page_limit
    end_idx = min(start_idx + page_limit, total_filtered)
    df_page = filtered.iloc[start_idx:end_idx].copy()

    # Render Cards or Table
    if "Cards" in flow_view_mode:
        st.caption(f"Displaying **{start_idx + 1}–{end_idx}** of **{total_filtered}** ranked {level_plural.lower()} (Click any card to inspect constituent equities)")
        render_analytical_card_grid(
            df_page,
            columns=2,
            key_prefix=f"flow_p{curr_page}",
            enable_selection=True,
            selected_entity=active_selected_entity
        )
        
        # Pagination Controls
        if total_pages > 1:
            pg_prev, pg_info, pg_next = st.columns([1, 2, 1])
            with pg_prev:
                if st.button("⬅ Previous Page", disabled=(curr_page == 1), key="btn_pg_prev", use_container_width=True):
                    st.session_state["flow_page_num"] = max(1, curr_page - 1)
                    st.rerun()
            with pg_info:
                st.markdown(f"<div style='text-align: center; font-size: 0.82rem; color: {t['text_muted']}; padding-top: 6px;'>Page <b>{curr_page}</b> of <b>{total_pages}</b> ({total_filtered} total {level_plural.lower()})</div>", unsafe_allow_html=True)
            with pg_next:
                if st.button("Next Page ➡", disabled=(curr_page == total_pages), key="btn_pg_next", use_container_width=True):
                    st.session_state["flow_page_num"] = min(total_pages, curr_page + 1)
                    st.rerun()
    else:
        disp_cols = [
            'Rank', 'entity_name', 'macro_sector', 'constituent_count',
            'current_strength', 'exp_return_20d', 'confidence_score', 'risk_score',
            'flow_state', 'trend_rating', 'final_action', 'breadth_qualification'
        ]
        if level_col == "macro_sector" and 'macro_sector' in disp_cols:
            disp_cols.remove('macro_sector')

        rename_map = {
            'entity_name': level_label,
            'macro_sector': 'Parent Sector',
            'constituent_count': 'Stocks (N)',
            'current_strength': 'Strength (Q1)',
            'exp_return_20d': '20D Exp Ret (%)',
            'confidence_score': 'Confidence (Q3)',
            'risk_score': 'Risk (Q4)',
            'flow_state': 'Flow State',
            'trend_rating': 'Trend Rating',
            'final_action': 'Action Recommendation',
            'breadth_qualification': 'Breadth Status'
        }
        df_disp = filtered[[c for c in disp_cols if c in filtered.columns]].rename(columns=rename_map)
        st.dataframe(
            df_disp,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Strength (Q1)": st.column_config.ProgressColumn("Strength (Q1)", format="%d", min_value=0, max_value=100),
                "Confidence (Q3)": st.column_config.ProgressColumn("Confidence (Q3)", format="%d", min_value=0, max_value=100),
                "Risk (Q4)": st.column_config.ProgressColumn("Risk (Q4)", format="%d", min_value=0, max_value=100),
                "20D Exp Ret (%)": st.column_config.NumberColumn("20D Exp Ret (%)", format="%.2f%%"),
            }
        )

    # 1-Click Drilldown Section
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.divider()

    drill_hdr_html = f"""<div style="margin-bottom: 8px;">
<h4 style="margin: 0; font-size: 1.05rem; font-weight: 800; color: {t['text_primary']};">🔎 1-CLICK CONSTITUENT STOCKS DRILLDOWN</h4>
<span style="font-size: 0.78rem; color: {t['text_muted']};">Select any {level_label.lower()} via the cards above or the dropdown below to inspect all universe-eligible equities</span>
</div>"""
    st.markdown(textwrap.dedent(drill_hdr_html).strip(), unsafe_allow_html=True)

    # Synchronized Dropdown
    selected_idx = drill_options.index(active_selected_entity) if active_selected_entity in drill_options else 0
    sel_entity = st.selectbox(
        f"Selected {level_label} ({len(drill_options)} available)",
        drill_options,
        index=selected_idx,
        key="flow_drill_sel"
    )
    
    if sel_entity != active_selected_entity:
        st.session_state["selected_drilldown_entity"] = sel_entity
        st.rerun()

    # Query constituent stocks matching ACTIVE_UNIVERSE strictly
    if sel_entity:
        conn = db.get_connection()
        
        # Enforce active universe filter on drilldown
        if u_ctx["is_filtered"]:
            if u_ctx["eligible_symbols"]:
                sym_list = list(u_ctx["eligible_symbols"])
                placeholders = ",".join(["?"] * len(sym_list))
                sql_stk = f"""
                SELECT s.symbol, s.company_name, s.macro_sector, s.industry, s.basic_industry,
                       COALESCE(m.close, p.close, 100.0) as close_price,
                       COALESCE(m.return_1d, 0.0) as return_1d,
                       COALESCE(m.return_5d, 0.0) as return_5d,
                       COALESCE(m.return_20d, 0.0) as return_20d,
                       COALESCE(m.rs_20d, 0.0) as rs_20d,
                       COALESCE(m.volume_ratio, 1.0) as volume_ratio,
                       COALESCE(m.above_50ema, 0) as above_50ema
                FROM stocks s
                LEFT JOIN stock_metrics m ON s.symbol = m.symbol AND m.date = ?
                LEFT JOIN daily_prices p ON s.symbol = p.symbol AND p.date = ?
                WHERE s.{level_col} = ? AND s.active = 1 AND s.symbol IN ({placeholders})
                ORDER BY COALESCE(m.rs_20d, 0.0) DESC
                """
                params = [selected_date, selected_date, sel_entity] + sym_list
                df_stk_view = pd.read_sql(sql_stk, conn, params=params)
            else:
                df_stk_view = pd.DataFrame()
        else:
            sql_stk = f"""
            SELECT s.symbol, s.company_name, s.macro_sector, s.industry, s.basic_industry,
                   COALESCE(m.close, p.close, 100.0) as close_price,
                   COALESCE(m.return_1d, 0.0) as return_1d,
                   COALESCE(m.return_5d, 0.0) as return_5d,
                   COALESCE(m.return_20d, 0.0) as return_20d,
                   COALESCE(m.rs_20d, 0.0) as rs_20d,
                   COALESCE(m.volume_ratio, 1.0) as volume_ratio,
                   COALESCE(m.above_50ema, 0) as above_50ema
            FROM stocks s
            LEFT JOIN stock_metrics m ON s.symbol = m.symbol AND m.date = ?
            LEFT JOIN daily_prices p ON s.symbol = p.symbol AND p.date = ?
            WHERE s.{level_col} = ? AND s.active = 1
            ORDER BY COALESCE(m.rs_20d, 0.0) DESC
            """
            params = [selected_date, selected_date, sel_entity]
            df_stk_view = pd.read_sql(sql_stk, conn, params=params)
        
        if not df_stk_view.empty:
            df_stk_disp = df_stk_view.rename(columns={
                'symbol': 'Symbol',
                'company_name': 'Company Name',
                'macro_sector': 'Sector',
                'industry': 'Major Industry',
                'basic_industry': 'Subsector',
                'close_price': 'Close Price (Rs)',
                'return_1d': '1D Ret (%)',
                'return_5d': '5D Ret (%)',
                'return_20d': '20D Ret (%)',
                'rs_20d': '20D RS (%)',
                'volume_ratio': 'Vol Ratio'
            })
            st.dataframe(
                df_stk_disp,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Close Price (Rs)": st.column_config.NumberColumn("Close Price (Rs)", format="Rs %.2f"),
                    "1D Ret (%)": st.column_config.NumberColumn("1D Ret (%)", format="%.2f%%"),
                    "5D Ret (%)": st.column_config.NumberColumn("5D Ret (%)", format="%.2f%%"),
                    "20D Ret (%)": st.column_config.NumberColumn("20D Ret (%)", format="%.2f%%"),
                    "20D RS (%)": st.column_config.NumberColumn("20D RS (%)", format="%.2f%%"),
                    "Vol Ratio": st.column_config.NumberColumn("Vol Ratio", format="%.2fx"),
                }
            )
            st.caption(f"Displaying all **{len(df_stk_view)}** eligible constituent stocks in **{sel_entity}** (Active Universe: **{u_ctx['chip_label']}**)")
        else:
            st.info(f"No active constituent equities match the active universe filter in **{sel_entity}**.")
