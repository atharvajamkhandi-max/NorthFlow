"""
Industries & Sectors Explorer: Comprehensive Sector Intelligence & Watchlist Hub.
Phase 71.1: Sanitized 2-Column Analytical Cards, Theme Switching & Deep Drilldown.
"""

import streamlit as st
import pandas as pd
import numpy as np
import textwrap
import io
import re
from database.db import Database
from dashboard.components.topbar import render_topbar
from dashboard.components.global_state import get_hierarchy_metadata, render_hierarchy_badge_inline
from dashboard.components.theme import get_theme_tokens, get_theme_mode
from dashboard.components.analytical_card import render_analytical_card, render_analytical_card_grid

@st.cache_data(ttl=120)
def load_sector_overview_data(selected_date: str, eligible_symbols: tuple = None):
    """
    Loads sector level aggregated performance metrics for the selected trading date,
    strictly respecting the active point-in-time eligible symbols filter.
    """
    db = Database()
    conn = db.get_connection()
    
    sql = """
    SELECT 
        v.symbol,
        v.company_name,
        v.sector,
        v.industry,
        v.index_membership,
        COALESCE(m.close, p.close, 100.0) as close,
        COALESCE(m.return_1d, 0.0) as return_1d,
        COALESCE(m.return_5d, 0.0) as return_5d,
        COALESCE(m.return_20d, 0.0) as return_20d,
        COALESCE(m.rs_20d, 0.0) as rs_20d,
        COALESCE(m.volume_ratio, 1.0) as volume_ratio,
        COALESCE(m.above_20ema, 0) as above_20ema,
        COALESCE(m.above_50ema, 0) as above_50ema,
        COALESCE(m.above_200ema, 0) as above_200ema,
        COALESCE(m.is_breakout_20d, 0) as is_breakout_20d,
        COALESCE(m.turnover, p.turnover, 100000.0) as turnover
    FROM stock_classification_master_v3 v
    LEFT JOIN stock_metrics m ON v.symbol = m.symbol AND m.date = ?
    LEFT JOIN daily_prices p ON v.symbol = p.symbol AND p.date = ?
    """
    df = pd.read_sql(sql, conn, params=[selected_date, selected_date])
    
    if df.empty or df['return_1d'].isna().all():
        latest_date = pd.read_sql("SELECT MAX(date) as max_d FROM stock_metrics", conn)['max_d'].iloc[0]
        if latest_date and latest_date != selected_date:
            df = pd.read_sql(sql, conn, params=[latest_date, latest_date])
            selected_date = latest_date
            
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    if eligible_symbols is not None:
        df = df[df['symbol'].isin(set(eligible_symbols))].copy()
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()

    sector_summary = df.groupby('sector').agg(
        stock_count=('symbol', 'count'),
        industry_count=('industry', 'nunique'),
        avg_return_1d=('return_1d', 'mean'),
        avg_return_5d=('return_5d', 'mean'),
        avg_return_20d=('return_20d', 'mean'),
        avg_rs_20d=('rs_20d', 'mean'),
        avg_volume_ratio=('volume_ratio', 'mean'),
        breadth_20=('above_20ema', lambda x: (x == 1).mean() * 100.0),
        breadth_50=('above_50ema', lambda x: (x == 1).mean() * 100.0),
        breakout_pct=('is_breakout_20d', lambda x: (x == 1).mean() * 100.0),
        total_turnover=('turnover', 'sum')
    ).reset_index()

    from config.model_v3_2_frozen import FROZEN_INDUSTRY_FACTOR_WEIGHTS
    w = FROZEN_INDUSTRY_FACTOR_WEIGHTS
    rs_norm = np.clip((sector_summary['avg_rs_20d'] + 15.0) / 30.0 * 100.0, 0.0, 100.0)
    vol_norm = np.clip(sector_summary['avg_volume_ratio'] / 2.0 * 100.0, 0.0, 100.0)
    sector_summary['strength_score'] = np.clip(
        w["breadth_50"] * sector_summary['breadth_50'] +
        w["relative_strength_20d"] * rs_norm +
        w["breadth_20"] * sector_summary['breadth_20'] +
        w["volume_strength"] * vol_norm,
        0.0, 100.0
    ).round(1)
    sector_summary['current_strength'] = sector_summary['strength_score']

    def classify_flow(row):
        score = row['strength_score']
        ret5 = row['avg_return_5d']
        b50 = row['breadth_50']
        if score >= 65.0 and b50 >= 50.0:
            return "LEADING", "#00D084"
        elif score >= 50.0 and ret5 > 0.0:
            return "ACCUMULATION", "#06B6D4"
        elif score < 40.0 and ret5 < -2.0:
            return "LAGGING", "#EF4444"
        elif score < 50.0 and ret5 < 0.0:
            return "WEAKENING", "#F59E0B"
        else:
            return "IMPROVING", "#A855F7"

    flow_res = sector_summary.apply(classify_flow, axis=1)
    sector_summary['flow_state'] = [r[0] for r in flow_res]
    sector_summary['flow_color'] = [r[1] for r in flow_res]

    return sector_summary, df

def render_industries_explorer(db: Database, selected_date: str):
    """
    Renders the interactive Sector & Industry Explorer with Deep-Dive and Watchlist Exporters.
    """
    from dashboard.components.universe_service import get_current_universe_context, render_universe_status_chip
    u_ctx = get_current_universe_context(selected_date)
    render_universe_status_chip(u_ctx)

    active_sector = st.session_state.get("explorer_active_sector", None)

    eligible_syms_tuple = u_ctx["eligible_symbols_tuple"] if u_ctx["is_filtered"] else None
    sector_summary, df_raw = load_sector_overview_data(selected_date, eligible_symbols=eligible_syms_tuple)
    if sector_summary.empty:
        st.warning(f"No sector data available for active market universe on session {selected_date}.")
        return

    all_sectors = sorted(sector_summary['sector'].tolist())

    if active_sector and active_sector in all_sectors:
        render_sector_deep_dive_page(active_sector, sector_summary, df_raw, all_sectors, selected_date)
    else:
        render_sector_directory_grid(sector_summary, df_raw, selected_date)

def render_sector_directory_grid(sector_summary: pd.DataFrame, df_raw: pd.DataFrame, selected_date: str):
    """
    Renders high-level Sector Directory with search, filters, and 2-column reference analytical cards.
    """
    t = get_theme_tokens()
    render_topbar(selected_date, page_title="Sector & Industry Directory")

    total_sectors = len(sector_summary)
    total_stocks = len(df_raw)
    leading_count = (sector_summary['flow_state'] == 'LEADING').sum()
    accum_count = (sector_summary['flow_state'] == 'ACCUMULATION').sum()
    avg_breadth = sector_summary['breadth_50'].mean()

    # KPI Strip
    strip_html = f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 16px;">
<div style="background-color: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 12px 16px;">
<div style="font-size: 0.70rem; font-weight: 700; color: {t['text_dim']}; text-transform: uppercase;">Total Macro Sectors</div>
<div style="font-size: 1.45rem; font-weight: 800; color: {t['text_primary']}; margin-top: 2px; font-family: 'JetBrains Mono';">{total_sectors}</div>
<div style="font-size: 0.72rem; color: {t['text_muted']}; margin-top: 2px;">2-Tier Clean Taxonomy</div>
</div>
<div style="background-color: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 12px 16px;">
<div style="font-size: 0.70rem; font-weight: 700; color: {t['text_dim']}; text-transform: uppercase;">Covered Equities</div>
<div style="font-size: 1.45rem; font-weight: 800; color: {t['accent']}; margin-top: 2px; font-family: 'JetBrains Mono';">{total_stocks:,}</div>
<div style="font-size: 0.72rem; color: {t['text_muted']}; margin-top: 2px;">Active Market Universe</div>
</div>
<div style="background-color: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 12px 16px;">
<div style="font-size: 0.70rem; font-weight: 700; color: {t['text_dim']}; text-transform: uppercase;">Leading / Accumulating</div>
<div style="font-size: 1.45rem; font-weight: 800; color: {t['positive']}; margin-top: 2px; font-family: 'JetBrains Mono';">{leading_count + accum_count}</div>
<div style="font-size: 0.72rem; color: {t['positive']}; margin-top: 2px;">{leading_count} Leading • {accum_count} Accum.</div>
</div>
<div style="background-color: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 12px 16px;">
<div style="font-size: 0.70rem; font-weight: 700; color: {t['text_dim']}; text-transform: uppercase;">Avg Sector Breadth</div>
<div style="font-size: 1.45rem; font-weight: 800; color: {t['warning']}; margin-top: 2px; font-family: 'JetBrains Mono';">{avg_breadth:.1f}%</div>
<div style="font-size: 0.72rem; color: {t['text_muted']}; margin-top: 2px;">Above 50 EMA</div>
</div>
</div>"""
    st.markdown(textwrap.dedent(strip_html).strip(), unsafe_allow_html=True)

    # Search & Sorting Controls
    c_search, c_sort, c_state, c_view = st.columns([3, 2, 2, 1.2])
    with c_search:
        search_query = st.text_input("🔍 Search Sector or Industry Name", placeholder="e.g. Rice, Jewellery, EMS, AI, Power, Defence, Finance...", key="sector_dir_search").strip().upper()
    with c_sort:
        sort_by = st.selectbox("Sort By", ["Strength Score (High to Low)", "Constituent Count (High to Low)", "1D Return (High to Low)", "5D Return (High to Low)", "20D Return (High to Low)"], index=0, key="sector_dir_sort")
    with c_state:
        state_filter = st.selectbox("Flow State Filter", ["All Flow States", "LEADING", "ACCUMULATION", "IMPROVING", "WEAKENING", "LAGGING"], index=0, key="sector_dir_state_filter")
    with c_view:
        sec_view_mode = st.radio("View", ["🗂️ Cards", "📊 Table"], horizontal=True, key="sec_view_mode_select", label_visibility="collapsed")

    df_filtered = sector_summary.copy()
    if search_query:
        matching_sectors_from_stocks = df_raw[
            df_raw['sector'].str.upper().str.contains(search_query, na=False) |
            df_raw['industry'].str.upper().str.contains(search_query, na=False) |
            df_raw['company_name'].str.upper().str.contains(search_query, na=False) |
            df_raw['symbol'].str.upper().str.contains(search_query, na=False)
        ]['sector'].unique()
        df_filtered = df_filtered[df_filtered['sector'].isin(matching_sectors_from_stocks)]

    if state_filter != "All Flow States":
        df_filtered = df_filtered[df_filtered['flow_state'] == state_filter]

    if "Strength Score" in sort_by:
        df_filtered = df_filtered.sort_values(by="strength_score", ascending=False)
    elif "Constituent Count" in sort_by:
        df_filtered = df_filtered.sort_values(by="stock_count", ascending=False)
    elif "1D Return" in sort_by:
        df_filtered = df_filtered.sort_values(by="avg_return_1d", ascending=False)
    elif "5D Return" in sort_by:
        df_filtered = df_filtered.sort_values(by="avg_return_5d", ascending=False)
    elif "20D Return" in sort_by:
        df_filtered = df_filtered.sort_values(by="avg_return_20d", ascending=False)

    df_filtered = df_filtered.reset_index(drop=True)
    df_filtered['Rank'] = np.arange(1, len(df_filtered) + 1)

    if df_filtered.empty:
        st.info(f"No sectors found matching search query '{search_query}'.")
        return

    # Cards View
    if "Cards" in sec_view_mode:
        cols = st.columns(2)
        for idx, sec_row in df_filtered.iterrows():
            sec_name = sec_row['sector']
            stock_cnt = int(sec_row['stock_count'])
            ind_cnt = int(sec_row['industry_count'])
            score = float(sec_row['strength_score'])
            ret5 = float(sec_row['avg_return_5d'])
            ret20 = float(sec_row['avg_return_20d'])
            b50 = float(sec_row['breadth_50'])
            flow_st = sec_row['flow_state']
            rank_num = int(sec_row['Rank'])
            
            card_html = render_analytical_card(
                rank=rank_num,
                title=sec_name,
                subtitle=f"{ind_cnt} sub-industries",
                action=flow_st,
                trend="Bullish" if b50 >= 50 else "Neutral",
                strength=score,
                exp_return_20d=ret20,
                breadth_50=b50,
                constituent_count=stock_cnt,
                extra_metric_label="5D RET",
                extra_metric_value=f"{ret5:+.1f}%"
            )
            with cols[idx % 2]:
                st.markdown(card_html, unsafe_allow_html=True)
                if st.button(f"⚡ Inspect {sec_name} ({stock_cnt} stocks) ➜", key=f"btn_sec_{sec_name}", use_container_width=True):
                    st.session_state["explorer_active_sector"] = sec_name
                    st.rerun()
    else:
        disp_df = df_filtered[[
            'Rank', 'sector', 'stock_count', 'industry_count',
            'strength_score', 'avg_return_1d', 'avg_return_5d', 'avg_return_20d',
            'breadth_20', 'breadth_50', 'flow_state'
        ]].rename(columns={
            'sector': 'Macro Sector',
            'stock_count': 'Stocks (N)',
            'industry_count': 'Sub-Industries',
            'strength_score': 'Strength Score',
            'avg_return_1d': '1D Ret (%)',
            'avg_return_5d': '5D Ret (%)',
            'avg_return_20d': '20D Ret (%)',
            'breadth_20': 'Breadth > 20 EMA (%)',
            'breadth_50': 'Breadth > 50 EMA (%)',
            'flow_state': 'Flow State'
        })
        st.dataframe(disp_df, use_container_width=True, hide_index=True)

def render_sector_deep_dive_page(sector_name: str, sector_summary: pd.DataFrame, df_raw: pd.DataFrame, all_sectors: list, selected_date: str):
    """
    Renders the dedicated sub-page for a single selected Sector with Watchlist Exporters and Constituent details.
    """
    t = get_theme_tokens()
    sec_row = sector_summary[sector_summary['sector'] == sector_name].iloc[0]
    stock_cnt = int(sec_row['stock_count'])
    score = float(sec_row['strength_score'])
    ret1 = float(sec_row['avg_return_1d'])
    ret5 = float(sec_row['avg_return_5d'])
    ret20 = float(sec_row['avg_return_20d'])
    flow_st = sec_row['flow_state']

    df_sec_stocks = df_raw[df_raw['sector'] == sector_name].copy()
    sub_industries = sorted(df_sec_stocks['industry'].unique().tolist())

    # --- TOP NAVIGATION & BREADCRUMBS ---
    nav_c1, nav_c2, nav_c3 = st.columns([1.5, 3.5, 2])
    with nav_c1:
        if st.button("⬅ Back to All Sectors", key="btn_back_to_dir", use_container_width=True):
            st.session_state["explorer_active_sector"] = None
            st.rerun()
    with nav_c2:
        bread_html = f"""<div style="font-size: 0.85rem; color: {t['text_dim']}; padding-top: 6px;">
<span style="color: {t['text_muted']};">Sectors Directory</span> &nbsp;›&nbsp; 
<b style="color: {t['text_primary']};">{sector_name}</b> &nbsp;({stock_cnt} Equities)
</div>"""
        st.markdown(textwrap.dedent(bread_html).strip(), unsafe_allow_html=True)
    with nav_c3:
        new_sec = st.selectbox("Switch Sector", all_sectors, index=all_sectors.index(sector_name), key="deepdive_sec_switcher", label_visibility="collapsed")
        if new_sec != sector_name:
            st.session_state["explorer_active_sector"] = new_sec
            st.rerun()

    # --- SECTOR HERO BANNER ---
    ret1_color = t["positive"] if ret1 > 0 else (t["negative"] if ret1 < 0 else t["text_muted"])
    ret5_color = t["positive"] if ret5 > 0 else (t["negative"] if ret5 < 0 else t["text_muted"])
    ret20_color = t["positive"] if ret20 > 0 else (t["negative"] if ret20 < 0 else t["text_muted"])

    hero_html = f"""<div style="background-color: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 16px 20px; margin: 12px 0 20px 0;">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
<div>
<div style="display: flex; align-items: center; gap: 12px;">
<h1 style="margin: 0; font-size: 1.5rem; font-weight: 800; color: {t['text_primary']};">{sector_name}</h1>
<span style="background-color: {t['positive_bg']}; color: {t['positive']}; border: 1px solid {t['positive_border']}; padding: 4px 10px; border-radius: 4px; font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">
{flow_st}
</span>
<span style="background-color: {t['accent_muted']}; color: {t['accent']}; padding: 4px 10px; border-radius: 4px; font-size: 0.78rem; font-weight: 700; font-family: 'JetBrains Mono';">
SCORE: {score:.1f} / 100
</span>
</div>
<div style="color: {t['text_muted']}; font-size: 0.82rem; margin-top: 6px;">
{stock_cnt} Listed Equities across {len(sub_industries)} Sub-Industries
</div>
</div>
<div style="display: flex; gap: 14px; align-items: center; text-align: center;">
<div style="background-color: {t['secondary_bg']}; border: 1px solid {t['card_border']}; border-radius: 6px; padding: 6px 14px;">
<div style="font-size: 0.65rem; color: {t['text_dim']}; font-weight: 700;">1D RETURN</div>
<div style="font-size: 0.95rem; font-weight: 800; color: {ret1_color}; font-family: 'JetBrains Mono';">{ret1:+.2f}%</div>
</div>
<div style="background-color: {t['secondary_bg']}; border: 1px solid {t['card_border']}; border-radius: 6px; padding: 6px 14px;">
<div style="font-size: 0.65rem; color: {t['text_dim']}; font-weight: 700;">5D RETURN</div>
<div style="font-size: 0.95rem; font-weight: 800; color: {ret5_color}; font-family: 'JetBrains Mono';">{ret5:+.2f}%</div>
</div>
<div style="background-color: {t['secondary_bg']}; border: 1px solid {t['card_border']}; border-radius: 6px; padding: 6px 14px;">
<div style="font-size: 0.65rem; color: {t['text_dim']}; font-weight: 700;">20D RETURN</div>
<div style="font-size: 0.95rem; font-weight: 800; color: {ret20_color}; font-family: 'JetBrains Mono';">{ret20:+.2f}%</div>
</div>
</div>
</div>
</div>"""
    st.markdown(textwrap.dedent(hero_html).strip(), unsafe_allow_html=True)

    # Watchlist Exporters
    st.markdown("### 📥 Export Watchlists")
    exp_c1, exp_c2, exp_c3 = st.columns(3)
    symbols_list = df_sec_stocks['symbol'].tolist()
    tv_data = "\n".join([f"NSE:{s}" for s in symbols_list])
    dhan_data = "\n".join(symbols_list)
    csv_buf = io.StringIO()
    df_sec_stocks.to_csv(csv_buf, index=False)

    with exp_c1:
        st.download_button("📈 TradingView Watchlist (.txt)", tv_data, file_name=f"{sector_name}_TradingView.txt", mime="text/plain", use_container_width=True)
    with exp_c2:
        st.download_button("📊 Dhan / Zerodha List (.txt)", dhan_data, file_name=f"{sector_name}_Symbols.txt", mime="text/plain", use_container_width=True)
    with exp_c3:
        st.download_button("📁 Full Constituents (.csv)", csv_buf.getvalue(), file_name=f"{sector_name}_Constituents.csv", mime="text/csv", use_container_width=True)

    # Constituents Table
    st.markdown(f"### 📋 {sector_name} Constituents ({stock_cnt})")
    st.dataframe(
        df_sec_stocks[['symbol', 'company_name', 'industry', 'close', 'return_1d', 'return_5d', 'return_20d', 'rs_20d', 'volume_ratio', 'above_50ema']],
        use_container_width=True,
        hide_index=True
    )
