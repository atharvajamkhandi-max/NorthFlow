"""
Industry Intelligence & Deep Dive Page (Phase 4).
Features:
- Dual-layer Classification Display: Official NSE Layer vs Custom Trading Layer
- Money Flow Methodology V2 Decomposed Architecture (6 Factor Breakdown & Trajectories)
- Statistical Reliability Rating (decoupled from score) & Constituent Sample Size
- Flow Confirmation (HIGH, MODERATE, CONFLICTING, LOW) & 2D Flow States
- Interactive Segment Filtering & Multi-Timeframe Performance
- Component Trajectory Tracking (Price, Breadth, Directional Volume, Trend, Breakouts, Delivery)
Benchmark: NIFTY SMALLCAP 250 (Explicitly labeled)
"""

import streamlit as st
import pandas as pd
from database.db import Database
from dashboard.components.topbar import render_topbar
from dashboard.components.charts import (
    create_industry_history_chart,
    create_relative_strength_chart,
    create_volume_participation_chart
)

def render_industry_detail(db: Database, selected_date: str):
    df_ind = db.get_latest_industry_metrics(trade_date=selected_date)
    if df_ind.empty:
        st.warning(f"No industry data found for session {selected_date}.")
        return

    all_industries = sorted(df_ind['basic_industry'].dropna().unique().tolist())
    
    if "selected_industry" not in st.session_state or st.session_state["selected_industry"] not in all_industries:
        st.session_state["selected_industry"] = "Electronic Manufacturing Services (EMS)" if "Electronic Manufacturing Services (EMS)" in all_industries else all_industries[0]

    selected_ind = st.session_state["selected_industry"]

    # --- BREADCRUMBS & NAVIGATION BAR ---
    b_col1, b_col2, b_col3 = st.columns([2.5, 2.5, 1])
    with b_col1:
        st.markdown(f"""
        <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 8px;">
            <span style="color: #94A3B8;">Market Overview</span> &nbsp;›&nbsp; 
            <span style="color: #94A3B8;">Industry Flow</span> &nbsp;›&nbsp; 
            <b style="color: #00D084;">{selected_ind}</b>
        </div>
        """, unsafe_allow_html=True)
    with b_col2:
        chosen = st.selectbox(
            "Switch Industry",
            all_industries,
            index=all_industries.index(selected_ind),
            key="intelligence_ind_picker",
            label_visibility="collapsed"
        )
        if chosen != selected_ind:
            st.session_state["selected_industry"] = chosen
            st.rerun()
    with b_col3:
        if st.button("← Back to Flow", key="back_to_flow_btn", use_container_width=True):
            st.session_state["nav_page"] = "🌊 Industry Flow"
            st.rerun()

    # Get Industry Meta Row
    row_ind = df_ind[df_ind['basic_industry'] == selected_ind].iloc[0] if not df_ind[df_ind['basic_industry'] == selected_ind].empty else None
    if row_ind is None:
        st.info("No metric data available for this industry.")
        return

    score_v1 = float(row_ind.get('score_today')) if pd.notna(row_ind.get('score_today')) else 50.0
    score_v2_raw = row_ind.get('score_v2')
    score_v2 = float(score_v2_raw) if pd.notna(score_v2_raw) and score_v2_raw is not None else score_v1
    status_v1 = str(row_ind.get('status', 'NEUTRAL'))
    flow_state_v2 = str(row_ind.get('flow_state_v2', status_v1))
    flow_conf = str(row_ind.get('flow_confirmation', 'MODERATE'))
    conflicts = str(row_ind.get('conflict_flags', 'NONE'))
    
    sc5_raw = row_ind.get('score_change_5d')
    score_change_5d = float(sc5_raw) if pd.notna(sc5_raw) and sc5_raw is not None else 0.0
    ret_5d = float(row_ind.get('avg_return_5d')) if pd.notna(row_ind.get('avg_return_5d')) else 0.0
    ret_20d = float(row_ind.get('avg_return_20d')) if pd.notna(row_ind.get('avg_return_20d')) else 0.0
    rs_5d = float(row_ind.get('industry_rs_5d')) if pd.notna(row_ind.get('industry_rs_5d')) else 0.0
    breadth_20 = float(row_ind.get('ema20_breadth')) if pd.notna(row_ind.get('ema20_breadth')) else 0.0
    vol_ratio = float(row_ind.get('avg_volume_ratio')) if pd.notna(row_ind.get('avg_volume_ratio')) else 1.0
    stock_count = int(row_ind.get('stock_count', 1)) if pd.notna(row_ind.get('stock_count')) else 1
    sector_name = str(row_ind.get('industry', 'N/A'))
    rel_score_raw = row_ind.get('reliability_score')
    rel_score = float(rel_score_raw) if pd.notna(rel_score_raw) and rel_score_raw is not None else 0.85
    rel_label_raw = row_ind.get('reliability_label')
    rel_label = str(rel_label_raw) if pd.notna(rel_label_raw) and rel_label_raw is not None else 'MODERATE'

    # Decomposed V2 Component Scores & Trajectories (with robust fallbacks)
    p_score = float(row_ind.get('price_score')) if pd.notna(row_ind.get('price_score')) else 50.0
    p_d5 = float(row_ind.get('price_score_change_5d')) if pd.notna(row_ind.get('price_score_change_5d')) else 0.0
    b_score = float(row_ind.get('breadth_score')) if pd.notna(row_ind.get('breadth_score')) else (float(row_ind.get('ema50_breadth')) if pd.notna(row_ind.get('ema50_breadth')) else 50.0)
    b_d5 = float(row_ind.get('breadth_score_change_5d')) if pd.notna(row_ind.get('breadth_score_change_5d')) else 0.0
    v_score = float(row_ind.get('volume_score')) if pd.notna(row_ind.get('volume_score')) else 50.0
    v_d5 = float(row_ind.get('volume_score_change_5d')) if pd.notna(row_ind.get('volume_score_change_5d')) else 0.0
    t_score = float(row_ind.get('trend_score')) if pd.notna(row_ind.get('trend_score')) else (float(row_ind.get('ema20_breadth')) if pd.notna(row_ind.get('ema20_breadth')) else 50.0)
    t_d5 = float(row_ind.get('trend_score_change_5d')) if pd.notna(row_ind.get('trend_score_change_5d')) else 0.0
    bk_score = float(row_ind.get('breakout_score')) if pd.notna(row_ind.get('breakout_score')) else 50.0
    bk_d5 = float(row_ind.get('breakout_score_change_5d')) if pd.notna(row_ind.get('breakout_score_change_5d')) else 0.0
    del_score = float(row_ind.get('delivery_score')) if pd.notna(row_ind.get('delivery_score')) else 40.0
    del_d5 = float(row_ind.get('delivery_score_change_5d')) if pd.notna(row_ind.get('delivery_score_change_5d')) else 0.0

    # Authoritative Active Universe Contract
    from dashboard.components.universe_service import get_current_universe_context, render_universe_status_chip
    u_ctx = get_current_universe_context(selected_date)
    render_universe_status_chip(u_ctx)

    # Fetch constituents with active universe filtering
    df_constituents = db.get_stocks_by_industry(selected_ind, trade_date=selected_date)
    if u_ctx["is_filtered"]:
        if not df_constituents.empty and u_ctx["eligible_symbols"]:
            df_constituents = df_constituents[df_constituents['symbol'].isin(u_ctx['eligible_symbols'])].copy()
        else:
            df_constituents = pd.DataFrame()

    stock_count = len(df_constituents)

    # If universe is filtered, recalculate active cross-sectional metrics
    if u_ctx["is_filtered"] and not df_constituents.empty:
        if 'above_20ema' in df_constituents.columns:
            breadth_20 = float((df_constituents['above_20ema'] == 1).mean() * 100.0)
            t_score = breadth_20
        if 'above_50ema' in df_constituents.columns:
            b_score = float((df_constituents['above_50ema'] == 1).mean() * 100.0)
        if 'return_5d' in df_constituents.columns:
            ret_5d = float(df_constituents['return_5d'].mean())
        if 'return_20d' in df_constituents.columns:
            ret_20d = float(df_constituents['return_20d'].mean())
        if 'rs_5d' in df_constituents.columns:
            rs_5d = float(df_constituents['rs_5d'].mean())
        if 'volume_ratio' in df_constituents.columns:
            vol_ratio = float(df_constituents['volume_ratio'].mean())
            v_score = np.clip(vol_ratio / 2.0 * 100.0, 0.0, 100.0)
    elif u_ctx["is_filtered"] and df_constituents.empty:
        stock_count = 0
        breadth_20 = 0.0
        b_score = 0.0
        ret_5d = 0.0
        ret_20d = 0.0
        rs_5d = 0.0
        vol_ratio = 0.0
        v_score = 0.0
        p_score = 0.0
        t_score = 0.0
        bk_score = 0.0
        del_score = 0.0
    
    with db.get_connection() as conn:
        q_cic = "SELECT symbol, custom_industry, custom_segment, notes FROM custom_industry_classification;"
        df_cic = pd.read_sql_query(q_cic, conn)

    if not df_constituents.empty and not df_cic.empty:
        df_constituents = pd.merge(df_constituents, df_cic, on='symbol', how='left')
    else:
        if not df_constituents.empty:
            df_constituents['custom_industry'] = None
            df_constituents['custom_segment'] = None
            df_constituents['notes'] = None

    custom_ind_names = df_constituents['custom_industry'].dropna().unique().tolist() if not df_constituents.empty else []
    custom_ind_display = ", ".join(custom_ind_names) if custom_ind_names else "Standard / Official"

    conf_colors = {
        "HIGH": "#00D084",
        "MODERATE": "#06B6D4",
        "CONFLICTING": "#EF4444",
        "LOW": "#64748B"
    }
    conf_color = conf_colors.get(flow_conf, "#06B6D4")

    # --- DUAL CLASSIFICATION & STATE HEADER BANNER ---
    st.markdown(f"""
    <div style="background-color: #111622; border: 1px solid #1E2638; border-radius: 6px; padding: 14px 18px; margin: 4px 0 16px 0;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
            <div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <h2 style="margin: 0; color: #F8FAFC; font-size: 1.35rem; font-weight: 700;">{selected_ind}</h2>
                    <span style="background-color: #161D2B; color: #00D084; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">
                        STATE: {flow_state_v2}
                    </span>
                    <span style="background-color: #161D2B; color: {conf_color}; border: 1px solid {conf_color}44; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600;">
                        CONFIRMATION: {flow_conf}
                    </span>
                </div>
                <div style="display: flex; gap: 18px; margin-top: 6px; font-size: 0.8rem; color: #94A3B8; flex-wrap: wrap;">
                    <span><b>Official Macro Sector:</b> {sector_name}</span>
                    <span><b>Custom Trading Group:</b> <span style="color: #06B6D4;">{custom_ind_display}</span></span>
                    <span><b>Constituents:</b> <span style="color: #F8FAFC; font-weight: 600;">{stock_count} Stocks</span></span>
                    <span><b>Reliability:</b> <span style="color: #F59E0B; font-weight: 600;">{rel_label} ({rel_score*100:.0f}%)</span></span>
                </div>
            </div>
            <div style="display: flex; gap: 12px; align-items: center;">
                <div style="text-align: right; background-color: #0A0D14; border: 1px solid #1E2638; padding: 6px 14px; border-radius: 4px;">
                    <div style="font-size: 0.68rem; color: #64748B; font-weight: 600;">MONEY FLOW V2 (RESEARCH)</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #00D084; font-family: 'JetBrains Mono', monospace;">
                        {score_v2:.1f} <span style="font-size: 0.75rem; color: {'#00D084' if score_change_5d >= 0 else '#EF4444'};">({score_change_5d:+.1f})</span>
                    </div>
                </div>
                <div style="text-align: right; background-color: #0A0D14; border: 1px solid #1E2638; padding: 6px 14px; border-radius: 4px;">
                    <div style="font-size: 0.68rem; color: #64748B; font-weight: 600;">PRODUCTION V1</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #94A3B8; font-family: 'JetBrains Mono', monospace;">
                        {score_v1:.1f}
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # If active conflict flags exist, show warning banner
    if conflicts != "NONE":
        st.markdown(f"""
        <div style="background-color: #1E1611; border-left: 3px solid #EF4444; border-top: 1px solid #3B2117; border-right: 1px solid #3B2117; border-bottom: 1px solid #3B2117; border-radius: 4px; padding: 8px 14px; margin-bottom: 12px; font-size: 0.8rem; color: #FCA5A5;">
            ⚠️ <b>Divergence Detected:</b> <code>{conflicts}</code> (Exercise caution: price or volume is diverging from broader constituent breadth).
        </div>
        """, unsafe_allow_html=True)

    # --- DECOMPOSED 6-FACTOR MONEY FLOW V2 BREAKDOWN STRIP ---
    st.markdown("##### 🔬 Decomposed Money Flow V2 Component Scores (0–100 Percentile)")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Price / RS (30%)", f"{p_score:.0f}", delta=f"5D: {p_d5:+.0f}")
    with c2:
        st.metric("Breadth (25%)", f"{b_score:.0f}", delta=f"5D: {b_d5:+.0f}")
    with c3:
        st.metric("Dir. Vol (20%)", f"{v_score:.0f}", delta=f"5D: {v_d5:+.0f}")
    with c4:
        st.metric("Trend Stack (10%)", f"{t_score:.0f}", delta=f"5D: {t_d5:+.0f}")
    with c5:
        st.metric("Breakouts (10%)", f"{bk_score:.0f}", delta=f"5D: {bk_d5:+.0f}")
    with c6:
        st.metric("Delivery (5%)", f"{del_score:.0f}", delta=f"5D: {del_d5:+.0f}")

    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

    # --- 5-STAT TECHNICAL SUMMARY STRIP ---
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("5D Return", f"{ret_5d:+.2f}%")
    with k2:
        st.metric("20D Return", f"{ret_20d:+.2f}%")
    with k3:
        st.metric("RS 5D vs SML250", f"{rs_5d:+.2f}%")
    with k4:
        st.metric("EMA20 Breadth", f"{breadth_20:.0f}%")
    with k5:
        st.metric("Avg Vol Ratio", f"{vol_ratio:.2f}x")

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # --- HISTORICAL CHARTS ---
    st.markdown("##### 📈 Historical Performance & Participation")
    with db.get_connection() as conn:
        q_hist = "SELECT * FROM industry_metrics WHERE basic_industry = ? ORDER BY date ASC;"
        df_hist = pd.read_sql_query(q_hist, conn, params=[selected_ind])

    ch_col1, ch_col2, ch_col3 = st.columns(3)
    with ch_col1:
        st.markdown("**Money Flow Score & Breadth**")
        fig_score = create_industry_history_chart(df_hist, selected_ind)
        st.plotly_chart(fig_score, use_container_width=True)
    with ch_col2:
        st.markdown("**RS vs NIFTY Smallcap 250**")
        fig_rs = create_relative_strength_chart(df_hist, selected_ind)
        st.plotly_chart(fig_rs, use_container_width=True)
    with ch_col3:
        st.markdown("**Volume Participation (vs 20D)**")
        fig_vol = create_volume_participation_chart(df_hist, selected_ind)
        st.plotly_chart(fig_vol, use_container_width=True)

    # --- CONSTITUENTS & LEADERSHIP SECTION ---
    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
    st.markdown("##### 🏆 Constituent Leadership & Segment Breakdown")

    if df_constituents.empty:
        st.info("No constituent stock records found for this industry.")
        return

    # Interactive Custom Segment Filter
    avail_segments = sorted(df_constituents['custom_segment'].dropna().unique().tolist())
    if avail_segments:
        seg_filter = st.multiselect(
            "Filter Constituents by Segment / Sub-Industry:",
            ["ALL"] + avail_segments,
            default=["ALL"],
            key=f"seg_filter_{selected_ind}"
        )
        if "ALL" not in seg_filter and seg_filter:
            df_constituents = df_constituents[df_constituents['custom_segment'].isin(seg_filter)]

    # Format Display Table
    df_constituents = df_constituents.sort_values('leadership_score', ascending=False).reset_index(drop=True)
    df_constituents['Rank'] = [f"#{i+1:02d}" for i in range(len(df_constituents))]

    disp_df = {
        'Rank': df_constituents['Rank'].tolist(),
        'Symbol': df_constituents['symbol'].tolist(),
        'Company': df_constituents['company_name'].tolist(),
        'Custom Segment': df_constituents['custom_segment'].fillna('-').tolist(),
        'Leadership Score': [f"{x:.1f}" if pd.notnull(x) else 'N/A' for x in df_constituents['leadership_score']],
        'Price (₹)': [f"{x:,.2f}" if pd.notnull(x) else 'N/A' for x in df_constituents['close']],
        '1D %': [f"{x:+.2f}%" if pd.notnull(x) else 'N/A' for x in df_constituents['return_1d']],
        '5D %': [f"{x:+.2f}%" if pd.notnull(x) else 'N/A' for x in df_constituents['return_5d']],
        '20D %': [f"{x:+.2f}%" if pd.notnull(x) else 'N/A' for x in df_constituents['return_20d']],
        'RS 5D vs SML250': [f"{x:+.2f}%" if pd.notnull(x) else 'N/A' for x in df_constituents['rs_5d']],
        'Vol Ratio': [f"{x:.2f}x" if pd.notnull(x) else 'N/A' for x in df_constituents['volume_ratio']],
        'Near High %': [f"{x:.1f}%" if pd.notnull(x) else 'N/A' for x in df_constituents['high_proximity']],
        'Trend Stack': ['✅' if x == 1 else '❌' for x in df_constituents['trend_stack']],
        'Breakout 20D': ['🔥' if x == 1 else '-' for x in df_constituents['is_breakout_20d']]
    }

    st.dataframe(pd.DataFrame(disp_df), use_container_width=True, hide_index=True, height=360)
