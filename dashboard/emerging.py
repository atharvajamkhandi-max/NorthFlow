"""
Emerging Rotations Page: Early Capital Rotation & Acceleration Screener.
Phase 71.2: Sanitized 2-Column Analytical Cards, Complete Ranking & View Modes.
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
from dashboard.components.early_radar_shadow_service import render_early_sector_radar_ui
from dashboard.components.theme import get_theme_tokens

def render_emerging(db: Database, selected_date: str):
    t = get_theme_tokens()
    meta = get_hierarchy_metadata()
    level_label = meta["label"]
    level_plural = meta["plural"]
    level_col = meta["col"]
    badge_html = render_hierarchy_badge_inline()

    render_topbar(selected_date, page_title=f"Emerging & Accelerating {level_plural}")

    from dashboard.components.universe_service import get_current_universe_context, render_universe_status_chip
    u_ctx = get_current_universe_context(selected_date)
    render_universe_status_chip(u_ctx)

    eligible_syms_tuple = u_ctx["eligible_symbols_tuple"] if u_ctx["is_filtered"] else None
    df_data, market_meta = get_aggregated_hierarchy_intelligence(selected_date, hierarchy_level_key=None, eligible_symbols=eligible_syms_tuple)
    if df_data.empty:
        st.warning(f"No data available for active market universe on session {selected_date}.")
        return

    df_emg = df_data[
        (df_data['final_action'].isin(['STRONG BUY', 'BUY', 'WATCH'])) |
        (df_data['score_change_5d'] > 2.0) |
        (df_data['flow_state'].isin(['ACCUMULATION', 'EXPANSION']))
    ].copy()
    df_emg = df_emg.sort_values('current_strength', ascending=False).reset_index(drop=True)
    df_emg['Rank'] = np.arange(1, len(df_emg) + 1)

    if df_emg.empty:
        st.info(f"No emerging rotational spikes detected at {level_label} level on this session.")
        return

    total_emg = len(df_emg)

    c_hdr, c_view, c_size = st.columns([2.5, 1.2, 1.3])
    with c_hdr:
        hdr_html = f"""<div style="margin-bottom: 8px;">
<div style="font-size: 1.15rem; font-weight: 800; color: {t['text_primary']}; letter-spacing: -0.01em;">
⚡ Top Accelerating & Emerging {level_plural}
</div>
<div style="font-size: 0.78rem; color: {t['text_muted']}; margin-top: 2px;">
Showing <b>{total_emg}</b> {level_plural.lower()} demonstrating institutional accumulation and upside momentum.
</div>
</div>"""
        st.markdown(textwrap.dedent(hdr_html).strip(), unsafe_allow_html=True)
    with c_view:
        view_mode = st.radio(
            "Display View",
            options=["🗂️ Cards View", "📊 Table View"],
            horizontal=True,
            key="emerging_view_mode",
            label_visibility="collapsed"
        )
    with c_size:
        emg_page_size = st.selectbox(
            "Page Size",
            options=["16 per page", "32 per page", "Show All"],
            index=0,
            key="emg_page_size_sel",
            label_visibility="collapsed"
        )

    limit = 16 if emg_page_size == "16 per page" else (32 if emg_page_size == "32 per page" else total_emg)
    df_display = df_emg.head(limit)

    if view_mode == "🗂️ Cards View":
        render_analytical_card_grid(df_display, columns=2, key_prefix="emg")
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
            'breadth_qualification': 'Qualification'
        }
        df_disp = df_display[[c for c in disp_cols if c in df_display.columns]].rename(columns=rename_map)
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

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
    st.divider()
    
    render_early_sector_radar_ui(selected_date)
