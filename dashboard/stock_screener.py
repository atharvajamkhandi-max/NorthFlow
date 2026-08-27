"""
Stock Screener Page: Cross-Industry & Subsector Quantitative Stock Screener.
Phase 71.1: Sanitized Monospace Screener Table & Theme Responsiveness.
"""

import streamlit as st
import pandas as pd
import numpy as np
import textwrap
from database.db import Database
from dashboard.components.topbar import render_topbar
from dashboard.components.global_state import get_hierarchy_metadata, render_hierarchy_badge_inline
from dashboard.components.theme import get_theme_tokens, get_theme_mode

def render_stock_screener(db: Database, selected_date: str):
    t = get_theme_tokens()
    meta = get_hierarchy_metadata()
    level_label = meta["label"]
    level_col = meta["col"]
    badge_html = render_hierarchy_badge_inline()

    render_topbar(selected_date, page_title="Quantitative Cross-Industry Stock Screener")

    from analytics.canonical_v3_2_service import get_canonical_stock_quant_score
    from dashboard.components.universe_service import get_current_universe_context, render_universe_status_chip
    u_ctx = get_current_universe_context(selected_date)
    render_universe_status_chip(u_ctx)

    df_stocks = get_canonical_stock_quant_score(selected_date)
    if u_ctx["is_filtered"]:
        if not df_stocks.empty:
            df_stocks = df_stocks[df_stocks['symbol'].isin(u_ctx['eligible_symbols'])].copy()
        else:
            df_stocks = pd.DataFrame()

    if df_stocks.empty or u_ctx["eligible_count"] == 0:
        st.warning(f"No eligible equities found in the active market universe ({u_ctx['chip_label']}) for session {selected_date}.")
        return

    hdr_html = f"""<div style="margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; background: {t['card_bg']}; padding: 8px 14px; border-radius: 6px; border: 1px solid {t['card_border']};">
<span style="font-size: 0.85rem; color: {t['text_muted']};">
Screening across <b style="color: {t['accent']};">{len(df_stocks):,}</b> active universe equities using quantitative factors and global {level_label.lower()} filters.
</span>
<div>{badge_html}</div>
</div>"""
    st.markdown(textwrap.dedent(hdr_html).strip(), unsafe_allow_html=True)

    # Filter Controls Bar (Row 1)
    f_c1, f_c2, f_c3 = st.columns([1.5, 1.5, 1.5])
    with f_c1:
        sec_list = ["All Macro Sectors"] + sorted(df_stocks['macro_sector'].dropna().unique().tolist())
        sel_sec = st.selectbox("1. Filter by Macro Sector", sec_list, index=0, key="scr_sec_sel")
    with f_c2:
        if sel_sec != "All Macro Sectors":
            sub_list = [f"All {meta['plural']}"] + sorted(df_stocks[df_stocks['macro_sector'] == sel_sec][level_col].dropna().unique().tolist())
        else:
            sub_list = [f"All {meta['plural']}"] + sorted(df_stocks[level_col].dropna().unique().tolist())
        sel_hier = st.selectbox(f"2. Filter by {level_label}", sub_list, index=0, key="scr_hier_sel")
    with f_c3:
        sel_action = st.selectbox("3. Filter by Stock Action", ["All Actions", "STRONG BUY", "BUY", "WATCH", "NEUTRAL", "REDUCE", "AVOID"], index=0, key="scr_act_sel")

    # Filter Controls Bar (Row 2)
    f_c4, f_c5, f_c6 = st.columns([1.5, 1.5, 2.0])
    with f_c4:
        min_lead_score = st.slider("Min Stock Strength", min_value=0.0, max_value=95.0, value=50.0, step=5.0, key="scr_min_score")
    with f_c5:
        sel_trend = st.selectbox("Trend Alignment", ["All Trends", "Above 50 EMA (Bullish)", "Below 50 EMA (Bearish)", "20D Breakouts Only"], index=0, key="scr_trend_sel")
    with f_c6:
        search_sym = st.text_input("🔍 Search Symbol / Company", placeholder="Type symbol or company name...", key="scr_search")

    filtered_df = df_stocks[df_stocks['stock_strength_score'] >= min_lead_score].copy()

    if sel_sec != "All Macro Sectors":
        filtered_df = filtered_df[filtered_df['macro_sector'] == sel_sec]

    if sel_hier != f"All {meta['plural']}":
        filtered_df = filtered_df[filtered_df[level_col] == sel_hier]

    if sel_action != "All Actions":
        filtered_df = filtered_df[filtered_df['final_action'] == sel_action]

    if sel_trend == "Above 50 EMA (Bullish)":
        filtered_df = filtered_df[filtered_df['above_50ema'] == 1]
    elif sel_trend == "Below 50 EMA (Bearish)":
        filtered_df = filtered_df[filtered_df['above_50ema'] == 0]
    elif sel_trend == "20D Breakouts Only":
        filtered_df = filtered_df[filtered_df['is_breakout_20d'] == 1]

    if search_sym.strip():
        q = search_sym.strip().lower()
        filtered_df = filtered_df[
            filtered_df['symbol'].str.lower().str.contains(q) |
            filtered_df['company_name'].str.lower().str.contains(q)
        ]

    filtered_df = filtered_df.sort_values('stock_strength_score', ascending=False).reset_index(drop=True)
    filtered_df['Rank'] = np.arange(1, len(filtered_df) + 1)

    sub_html = f"""<div style="display: flex; justify-content: space-between; align-items: center; margin: 12px 0 8px 0;">
<span style="font-size: 0.9rem; font-weight: 700; color: {t['text_muted']};">MATCHING EQUITIES: <b style="color: {t['accent']};">{len(filtered_df)}</b> / {len(df_stocks)}</span>
</div>"""
    st.markdown(textwrap.dedent(sub_html).strip(), unsafe_allow_html=True)

    if filtered_df.empty:
        st.info("No equities match the selected criteria.")
        return

    if level_col == "macro_sector":
        disp_cols = [
            'Rank', 'symbol', 'company_name', 'macro_sector',
            'close_price', 'stock_strength_score', 'return_1d', 'return_5d', 'return_20d',
            'rs_20d', 'volume_ratio', 'final_action'
        ]
        rename_map = {
            'symbol': 'Symbol',
            'company_name': 'Company Name',
            'macro_sector': 'Macro Sector',
            'close_price': 'Price (Rs)',
            'stock_strength_score': 'Score',
            'return_1d': '1D %',
            'return_5d': '5D %',
            'return_20d': '20D %',
            'rs_20d': '20D RS',
            'volume_ratio': 'Vol Ratio',
            'final_action': 'Action'
        }
    else:
        disp_cols = [
            'Rank', 'symbol', 'company_name', 'macro_sector', level_col,
            'close_price', 'stock_strength_score', 'return_1d', 'return_5d', 'return_20d',
            'rs_20d', 'volume_ratio', 'final_action'
        ]
        rename_map = {
            'symbol': 'Symbol',
            'company_name': 'Company Name',
            'macro_sector': 'Sector',
            level_col: level_label,
            'close_price': 'Price (Rs)',
            'stock_strength_score': 'Score',
            'return_1d': '1D %',
            'return_5d': '5D %',
            'return_20d': '20D %',
            'rs_20d': '20D RS',
            'volume_ratio': 'Vol Ratio',
            'final_action': 'Action'
        }

    df_disp = filtered_df[[c for c in disp_cols if c in filtered_df.columns]].rename(columns=rename_map)

    st.dataframe(
        df_disp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100),
            "Price (Rs)": st.column_config.NumberColumn("Price (Rs)", format="Rs %.2f"),
            "1D %": st.column_config.NumberColumn("1D %", format="%.2f%%"),
            "5D %": st.column_config.NumberColumn("5D %", format="%.2f%%"),
            "20D %": st.column_config.NumberColumn("20D %", format="%.2f%%"),
            "20D RS": st.column_config.NumberColumn("20D RS", format="%.2f%%"),
            "Vol Ratio": st.column_config.NumberColumn("Vol Ratio", format="%.2fx"),
        }
    )
