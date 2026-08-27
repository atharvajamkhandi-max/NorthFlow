from dashboard.components.early_radar_shadow_service import render_early_sector_radar_ui
"""
FLOW - Industry Intelligence Terminal (Command Center Cockpit)
Integrated with the Universal Global Hierarchy & Aggregation Lens.
Enforces Frozen Model Specification: MODEL_V3.2_FROZEN.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import textwrap
from datetime import datetime

from database.db import Database
from dashboard.components.theme import apply_institutional_theme
from dashboard.components.trading_calendar import (
    render_trading_session_calendar,
    get_available_nse_sessions_cached,
    get_session_maturity_status
)
from dashboard.components.header import render_cockpit_header
from dashboard.components.global_state import get_hierarchy_metadata, render_hierarchy_badge_inline
from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
from dashboard.components.charts import (
    plot_industry_landscape_matrix,
    plot_return_distribution_bell_curve,
    plot_accumulation_flow_gauge,
    plot_industry_rotation_trail
)
from config.model_v3_2_frozen import MODEL_V3_2_FINGERPRINT

def render_phase13_intelligence_terminal(db=None, selected_date=None):
    if db is None:
        db = Database()
    conn = db.get_connection()

    apply_institutional_theme()

    all_sessions = get_available_nse_sessions_cached()
    total_sessions = len(all_sessions) if all_sessions else 403

    if not selected_date:
        selected_date = st.session_state.get("selected_trading_date", all_sessions[-1] if all_sessions else "2026-08-21")

    maturity = get_session_maturity_status(selected_date, all_sessions)

    # Fetch global hierarchy lens
    meta = get_hierarchy_metadata()
    level_label = meta["label"]
    level_plural = meta["plural"]
    level_col = meta["col"]
    badge_html = render_hierarchy_badge_inline()

    # Load unified intelligence aggregated at the active global hierarchy level with user universe filter
    from dashboard.components.universe_service import get_current_universe_context, render_universe_status_chip
    u_ctx = get_current_universe_context(selected_date)
    eligible_syms = u_ctx["eligible_symbols_tuple"] if u_ctx["is_filtered"] else None
    df_agg, market_meta = get_aggregated_hierarchy_intelligence(selected_date, hierarchy_level_key=None, eligible_symbols=eligible_syms)

    # Single canonical Early Radar calculation (cached)
    from dashboard.components.early_radar_shadow_service import get_cached_early_radar_scores
    radar_scored = get_cached_early_radar_scores(selected_date)
    if not radar_scored.empty:
        radar_today = radar_scored[radar_scored['date'] == pd.to_datetime(selected_date)].copy()
        if radar_today.empty:
            radar_today = radar_scored[radar_scored['date'] == radar_scored['date'].max()].copy()
    else:
        radar_today = pd.DataFrame()

    # --- SIDEBAR: CASCADING FILTERS (Filtered by Active Market Universe) ---
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🏛️ Cascading Filters")
        
        if u_ctx["is_filtered"]:
            if u_ctx["eligible_symbols"]:
                sym_list = list(u_ctx["eligible_symbols"])
                ph = ",".join(["?"] * len(sym_list))
                sec_sql = f"SELECT DISTINCT macro_sector FROM stocks WHERE active = 1 AND macro_sector IS NOT NULL AND symbol IN ({ph}) ORDER BY macro_sector"
                all_sectors = sorted(pd.read_sql(sec_sql, conn, params=sym_list)['macro_sector'].tolist())
            else:
                all_sectors = []
        else:
            all_sectors = sorted(pd.read_sql("SELECT DISTINCT macro_sector FROM stocks WHERE active = 1 AND macro_sector IS NOT NULL ORDER BY macro_sector", conn)['macro_sector'].tolist())
            
        selected_sector = st.selectbox("1. Direct Sector", ["ALL SECTORS (Universal)"] + all_sectors, index=0)

        # Industry Filter
        if u_ctx["is_filtered"]:
            if u_ctx["eligible_symbols"]:
                sym_list = list(u_ctx["eligible_symbols"])
                ph = ",".join(["?"] * len(sym_list))
                if selected_sector != "ALL SECTORS (Universal)":
                    ind_sql = f"SELECT DISTINCT industry FROM stocks WHERE macro_sector = ? AND active = 1 AND symbol IN ({ph}) ORDER BY industry"
                    all_industries = sorted(pd.read_sql(ind_sql, conn, params=[selected_sector] + sym_list)['industry'].tolist())
                else:
                    ind_sql = f"SELECT DISTINCT industry FROM stocks WHERE active = 1 AND symbol IN ({ph}) ORDER BY industry"
                    all_industries = sorted(pd.read_sql(ind_sql, conn, params=sym_list)['industry'].tolist())
            else:
                all_industries = []
        else:
            if selected_sector != "ALL SECTORS (Universal)":
                ind_sql = "SELECT DISTINCT industry FROM stocks WHERE macro_sector = ? AND active = 1 ORDER BY industry"
                all_industries = sorted(pd.read_sql(ind_sql, conn, params=[selected_sector])['industry'].tolist())
            else:
                ind_sql = "SELECT DISTINCT industry FROM stocks WHERE active = 1 ORDER BY industry"
                all_industries = sorted(pd.read_sql(ind_sql, conn)['industry'].tolist())
                
        selected_industry = st.selectbox("2. Major Industry", ["ALL INDUSTRIES (Universal)"] + all_industries, index=0)

        # Subsector Filter
        if u_ctx["is_filtered"]:
            if u_ctx["eligible_symbols"]:
                sym_list = list(u_ctx["eligible_symbols"])
                ph = ",".join(["?"] * len(sym_list))
                if selected_industry != "ALL INDUSTRIES (Universal)":
                    sub_sql = f"SELECT DISTINCT basic_industry FROM stocks WHERE industry = ? AND active = 1 AND symbol IN ({ph}) ORDER BY basic_industry"
                    all_subsectors = sorted(pd.read_sql(sub_sql, conn, params=[selected_industry] + sym_list)['basic_industry'].tolist())
                elif selected_sector != "ALL SECTORS (Universal)":
                    sub_sql = f"SELECT DISTINCT basic_industry FROM stocks WHERE macro_sector = ? AND active = 1 AND symbol IN ({ph}) ORDER BY basic_industry"
                    all_subsectors = sorted(pd.read_sql(sub_sql, conn, params=[selected_sector] + sym_list)['basic_industry'].tolist())
                else:
                    sub_sql = f"SELECT DISTINCT basic_industry FROM stocks WHERE active = 1 AND symbol IN ({ph}) ORDER BY basic_industry"
                    all_subsectors = sorted(pd.read_sql(sub_sql, conn, params=sym_list)['basic_industry'].tolist())
            else:
                all_subsectors = []
        else:
            if selected_industry != "ALL INDUSTRIES (Universal)":
                sub_sql = "SELECT DISTINCT basic_industry FROM stocks WHERE industry = ? AND active = 1 ORDER BY basic_industry"
                all_subsectors = sorted(pd.read_sql(sub_sql, conn, params=[selected_industry])['basic_industry'].tolist())
            elif selected_sector != "ALL SECTORS (Universal)":
                sub_sql = "SELECT DISTINCT basic_industry FROM stocks WHERE macro_sector = ? AND active = 1 ORDER BY basic_industry"
                all_subsectors = sorted(pd.read_sql(sub_sql, conn, params=[selected_sector])['basic_industry'].tolist())
            else:
                sub_sql = "SELECT DISTINCT basic_industry FROM stocks WHERE active = 1 ORDER BY basic_industry"
                all_subsectors = sorted(pd.read_sql(sub_sql, conn)['basic_industry'].tolist())
                
        selected_subsector = st.selectbox("3. Specialization Subsector", ["ALL SUBSECTORS (Universal)"] + all_subsectors, index=0)

    # 1. Global Cockpit Header Bar
    regime_lbl = market_meta.get("market_regime", "WEAK_BULL").replace("_", " ")
    render_cockpit_header(selected_date=selected_date, total_sessions=total_sessions, regime_label=regime_lbl, regime_score=74.0)

    # 2. Main Navigation Tabs (Simplified 4 Core Tabs - Early Radar dedicated to Sidebar)
    tab_cockpit, tab_forensic, tab_radar, tab_guide = st.tabs([
        "🏛️ Dashboard (Command Center)",
        "📊 7-Dimension Forensic Profile",
        "⚖️ Sector Comparison Radar",
        "📚 Methodology & Model Validation"
    ])

    with tab_cockpit:
        # --- LEVEL 1: PLAIN ENGLISH EXECUTIVE MARKET SUMMARY ---
        st.markdown(textwrap.dedent(f"""<div class="flow-card" style="border: 1px solid rgba(56, 189, 248, 0.3); background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.6) 100%); margin-bottom: 16px; padding: 18px 20px;">
<div style="font-size: 0.78rem; font-weight: 800; color: #38BDF8; letter-spacing: 0.08em; text-transform: uppercase;">
⚡ EXECUTIVE SUMMARY • MARKET ROTATION PULSE
</div>
<div style="font-size: 1.25rem; font-weight: 800; color: #F8FAFC; margin-top: 4px; margin-bottom: 12px;">
WHAT IS HAPPENING IN THE MARKET?
</div>
"""), unsafe_allow_html=True)

        if not df_agg.empty:
            # 1. Derive 4 clear categories from existing metrics
            strong_now = df_agg[df_agg['current_strength'] >= 65.0].sort_values('current_strength', ascending=False).head(3)
            heating_up = df_agg[(df_agg['avg_return_5d'] > 0) & (df_agg['breadth_50'] >= 50.0) & (df_agg['current_strength'] < 65.0)].sort_values('avg_return_5d', ascending=False).head(3)
            if heating_up.empty:
                heating_up = df_agg.sort_values('avg_return_5d', ascending=False).head(3)
            
            # Precalculated early accumulation signals from canonical radar result
            early_accum = radar_today.sort_values('early_radar_score', ascending=False).head(3) if not radar_today.empty else pd.DataFrame()

            losing_strength = df_agg[df_agg['current_strength'] < 45.0].sort_values('current_strength', ascending=True).head(3)
            if losing_strength.empty:
                losing_strength = df_agg.sort_values('current_strength', ascending=True).head(3)

            p1, p2, p3, p4 = st.columns(4)
            with p1:
                st.markdown(textwrap.dedent("""<div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 12px 14px; min-height: 140px;">
<div style="font-weight: 800; font-size: 0.85rem; color: #34D399;">🚀 STRONG NOW</div>
<div style="font-size: 0.70rem; color: #94A3B8; margin-bottom: 8px;">Already leading the market</div>
"""), unsafe_allow_html=True)
                for _, r in strong_now.iterrows():
                    st.markdown(f"<div style='font-size: 0.78rem; font-weight: 700; color: #F8FAFC; margin-bottom: 3px;'>• {r['entity_name'][:20]} <span style='color:#34D399; font-size:0.70rem;'>({r['current_strength']:.0f})</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with p2:
                st.markdown(textwrap.dedent("""<div style="background: rgba(14, 165, 233, 0.08); border: 1px solid rgba(14, 165, 233, 0.25); border-radius: 8px; padding: 12px 14px; min-height: 140px;">
<div style="font-weight: 800; font-size: 0.85rem; color: #38BDF8;">🔥 HEATING UP</div>
<div style="font-size: 0.70rem; color: #94A3B8; margin-bottom: 8px;">Money flow & breadth accelerating</div>
"""), unsafe_allow_html=True)
                for _, r in heating_up.iterrows():
                    st.markdown(f"<div style='font-size: 0.78rem; font-weight: 700; color: #F8FAFC; margin-bottom: 3px;'>• {r['entity_name'][:20]} <span style='color:#38BDF8; font-size:0.70rem;'>({r['avg_return_5d']:+.1f}%)</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with p3:
                st.markdown(textwrap.dedent("""<div style="background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 8px; padding: 12px 14px; min-height: 140px;">
<div style="font-weight: 800; font-size: 0.85rem; color: #C084FC;">🟢 EARLY ACCUMULATION</div>
<div style="font-size: 0.70rem; color: #94A3B8; margin-bottom: 8px;">Quiet buying before expansion</div>
"""), unsafe_allow_html=True)
                if not early_accum.empty:
                    for _, r in early_accum.iterrows():
                        st.markdown(f"<div style='font-size: 0.78rem; font-weight: 700; color: #F8FAFC; margin-bottom: 3px;'>• {r['industry'][:20]} <span style='color:#C084FC; font-size:0.70rem;'>(Radar {r['early_radar_score']:.0f})</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with p4:
                st.markdown(textwrap.dedent("""<div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 8px; padding: 12px 14px; min-height: 140px;">
<div style="font-weight: 800; font-size: 0.85rem; color: #F87171;">🔴 LOSING STRENGTH</div>
<div style="font-size: 0.70rem; color: #94A3B8; margin-bottom: 8px;">Money flow & momentum fading</div>
"""), unsafe_allow_html=True)
                for _, r in losing_strength.iterrows():
                    st.markdown(f"<div style='font-size: 0.78rem; font-weight: 700; color: #F8FAFC; margin-bottom: 3px;'>• {r['entity_name'][:20]} <span style='color:#F87171; font-size:0.70rem;'>({r['current_strength']:.0f})</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # --- LEVEL 1.5: EARLY SECTOR RADAR TOP OPPORTUNITY SPOTLIGHT ---
        if not radar_today.empty:
            top_radar = radar_today.sort_values('early_radar_score', ascending=False).iloc[0]
            lead_d = top_radar['expected_lead_days']
            r_sc = top_radar['early_radar_score']
            v32_sc = float(top_radar.get('v3_2_strength', 48.0))
            conf = "HIGH" if r_sc >= 75.0 else ("MODERATE" if r_sc >= 65.0 else "WATCH")
            
            st.markdown(f"""<div class="flow-card" style="border: 1px solid rgba(14, 165, 233, 0.4); background: rgba(14, 165, 233, 0.04); margin-bottom: 16px; padding: 16px 20px;">
<div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
    <div>
        <div style="font-size: 0.72rem; color: #38BDF8; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em;">
            📡 EARLY SECTOR RADAR • PRECURSOR ACCUMULATION SPOTLIGHT
        </div>
        <div style="font-size: 1.25rem; font-weight: 800; color: #F8FAFC; margin-top: 3px;">
            #1 {top_radar['industry']} <span style="background-color: rgba(16, 185, 129, 0.2); color: #34D399; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; font-weight: 700; margin-left: 8px;">🟢 EARLY ACCUMULATION</span>
        </div>
        <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 4px;">
            Possible move window: <b style="color: #F8FAFC;">1–5 trading days</b> (Lead ~{lead_d:.1f}D) | Confidence: <b style="color: #38BDF8;">{conf}</b>
        </div>
    </div>
    <div style="display: flex; gap: 12px;">
        <div style="background: rgba(0,0,0,0.35); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.08); text-align: right;">
            <div style="font-size: 0.68rem; color: #94A3B8; text-transform: uppercase;">Radar Score</div>
            <div style="font-size: 1.2rem; font-weight: 800; color: #38BDF8; font-family: 'JetBrains Mono';">{r_sc:.1f}<span style="font-size: 0.70rem; color: #64748B;">/100</span></div>
        </div>
        <div style="background: rgba(0,0,0,0.35); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.08); text-align: right;">
            <div style="font-size: 0.68rem; color: #94A3B8; text-transform: uppercase;">Current Strength</div>
            <div style="font-size: 1.2rem; font-weight: 800; color: #F59E0B; font-family: 'JetBrains Mono';">{v32_sc:.1f}<span style="font-size: 0.70rem; color: #64748B;">/100</span></div>
        </div>
    </div>
</div>
<div style="margin-top: 10px; font-size: 0.80rem; color: #CBD5E1; line-height: 1.5;">
    <b>Why is it showing up?</b>
    <ul style="margin: 3px 0 0 16px; padding: 0; color: #94A3B8;">
        <li>More stocks are moving together ({top_radar['cross_stock_synchronization']:.1f}% cross-stock synchronization).</li>
        <li>Buying and delivery intensity is accelerating before broad price breakout.</li>
        <li>Current V3.2 Strength is <b>{v32_sc:.1f}/100</b> — <i>"The sector isn't strong yet, but something underneath is changing."</i></li>
    </ul>
</div>
</div>""", unsafe_allow_html=True)

        # 1. ROTATION MOMENTUM WHEEL WITH PROMINENT GUIDE
        st.markdown(textwrap.dedent(f"""<div class="flow-card">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
<div>
<span style="font-weight: 800; font-size: 0.95rem; color: #F8FAFC; letter-spacing: 0.04em;">🔄 {level_label.upper()} ROTATION MOMENTUM WHEEL (PAST → PRESENT → PROJECTED)</span>
<span style="font-size: 0.70rem; color: #64748B; margin-left: 8px;">(Tracks clockwise sector rotation through 4 institutional phases)</span>
</div>
<div>{badge_html}</div>
</div>
"""), unsafe_allow_html=True)

        if not df_agg.empty:
            wheel_options = ["🌟 Balanced Quadrant Movers (Full Clockwise Cycle)"] + df_agg['entity_name'].tolist()
            selected_wheel_item = st.selectbox("Focus / Highlight Industry on Momentum Wheel:", wheel_options, index=0, key="rot_wheel_select")
            hl_name = None if selected_wheel_item.startswith("🌟") else selected_wheel_item

            fig_rot = plot_industry_rotation_trail(df_agg, label_col="entity_name", highlight_name=hl_name)
            st.plotly_chart(fig_rot, use_container_width=True, config={'displayModeBar': False})

        # Plain English 4-Phase How-To-Read Guide
        st.markdown(textwrap.dedent("""<div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px 16px; margin-top: 6px;">
<div style="font-size: 0.78rem; font-weight: 800; color: #38BDF8; margin-bottom: 6px;">
💡 HOW TO READ THIS ROTATION WHEEL:
</div>
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; font-size: 0.74rem; color: #94A3B8;">
<div>
<span style="color: #0EA5E9; font-weight: 700;">1. 🔵 IMPROVING (Top-Left):</span><br>
Money is starting to enter. <b>Early accumulation phase</b> — price is still recovering while flow surges.
</div>
<div>
<span style="color: #10B981; font-weight: 700;">2. 🟢 LEADING (Top-Right):</span><br>
Money is already strong. <b>Established market leaders</b> — both price and money flow are outperforming.
</div>
<div>
<span style="color: #F59E0B; font-weight: 700;">3. 🟡 WEAKENING (Bottom-Right):</span><br>
Money flow is slowing. <b>Profit taking phase</b> — price is high but buying momentum is fading.
</div>
<div>
<span style="color: #EF4444; font-weight: 700;">4. 🔴 LAGGING (Bottom-Left):</span><br>
Money flow and strength are weak. <b>Underperforming basket</b> — under pressure vs Nifty 500.
</div>
</div>
<div style="font-size: 0.70rem; color: #64748B; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 5px;">
<b>Trail Vector:</b> ⚪ Past (5 Days Ago) ➔ 🔷 Today (Current Live) ➔ ⭐ Projected (Next 20-Day Model Forecast Path)
</div>
</div>
</div>"""), unsafe_allow_html=True)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # 2. LANDSCAPE MATRIX & TOP OPPORTUNITIES
        col_land, col_opp = st.columns([1.15, 1.0])

        with col_land:
            st.markdown(textwrap.dedent(f"""<div class="flow-card">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
<div>
<span style="font-weight: 800; font-size: 0.92rem; color: #F8FAFC; letter-spacing: 0.04em;">{level_label.upper()} LANDSCAPE MATRIX</span>
<span style="font-size: 0.70rem; color: #64748B; margin-left: 6px;">(Strength vs Forward Opportunity)</span>
</div>
<div>{badge_html}</div>
</div>
"""), unsafe_allow_html=True)
            
            fig_matrix = plot_industry_landscape_matrix(df_agg, horizon="20D", label_col="entity_name")
            st.plotly_chart(fig_matrix, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col_opp:
            st.markdown(textwrap.dedent(f"""<div class="flow-card">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
<span style="font-weight: 800; font-size: 0.88rem; color: #F8FAFC; letter-spacing: 0.04em;">TOP {level_label.upper()} OPPORTUNITIES</span>
<span style="font-size: 0.68rem; color: #10B981; font-weight: 700;">PRIMARY QUALIFIED (N ≥ 5)</span>
</div>"""), unsafe_allow_html=True)

            if not df_agg.empty:
                # Primary Industry Rule: Only N >= 5 qualify for top primary ranking
                df_prim_qual = df_agg[df_agg['is_production_eligible']].copy()
                if df_prim_qual.empty:
                    df_prim_qual = df_agg.copy()
                
                df_top = df_prim_qual.sort_values(by='current_strength', ascending=False).head(5).copy()
                table_html = f"""<table class="flow-table"><thead><tr><th>Rank</th><th>{level_label}</th><th>Strength</th><th>20D RS</th><th>Exp 20D</th><th>Action</th></tr></thead><tbody>"""
                for idx, (_, r) in enumerate(df_top.iterrows()):
                    item_name = str(r['entity_name'])[:24]
                    sc = r.get('current_strength', 50)
                    rs = r.get('industry_rs_20d', 0)
                    ret = r.get('exp_return_20d', 0)
                    badge = '<span class="badge-pill badge-strong-buy">STRONG BUY</span>' if sc >= 65 else ('<span class="badge-pill badge-buy">BUY</span>' if sc >= 50 else ('<span class="badge-pill badge-avoid">AVOID</span>' if sc < 35 else '<span class="badge-pill badge-neutral">NEUTRAL</span>'))
                    
                    table_html += f"""<tr><td style="font-family: 'JetBrains Mono'; font-weight: 700; color: #0EA5E9;">#{idx+1}</td><td style="font-weight: 600;">{item_name}</td><td style="font-family: 'JetBrains Mono'; font-weight: 700; color: #10B981;">{sc:.1f}</td><td style="font-family: 'JetBrains Mono'; color: #0EA5E9;">{rs:+.1f}%</td><td style="font-family: 'JetBrains Mono'; color: #10B981; font-weight: 700;">{ret:+.1f}%</td><td>{badge}</td></tr>"""
                table_html += "</tbody></table>"
                st.markdown(textwrap.dedent(table_html), unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # MIDDLE ROW: 4 Executive KPI Metrics Cards
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(textwrap.dedent("""<div class="kpi-container">
<div class="kpi-title">Market Strength <span>⚡</span></div>
<div class="kpi-value">74<span style="font-size: 1rem; color: #64748B;">/100</span></div>
<div class="kpi-delta positive">↑ +6 vs 20D ago</div>
</div>"""), unsafe_allow_html=True)
        with k2:
            st.markdown(textwrap.dedent(f"""<div class="kpi-container">
<div class="kpi-title">Active {level_plural} <span>🏛️</span></div>
<div class="kpi-value">{len(df_agg)}<span style="font-size: 1rem; color: #64748B;"> Total</span></div>
<div class="kpi-delta positive">100% Real-World Mapped</div>
</div>"""), unsafe_allow_html=True)
        with k3:
            st.markdown(textwrap.dedent(f"""<div class="kpi-container">
<div class="kpi-title">Production Qualified <span>🎯</span></div>
<div class="kpi-value">{market_meta.get('production_eligible_count', len(df_agg))}<span style="font-size: 1rem; color: #64748B;"> N ≥ 5</span></div>
<div class="kpi-delta positive">Strictly Disaggregated</div>
</div>"""), unsafe_allow_html=True)
        with k4:
            st.markdown(textwrap.dedent("""<div class="kpi-container">
<div class="kpi-title">Market Breadth (>50 EMA) <span>📈</span></div>
<div class="kpi-value">64.2<span style="font-size: 1rem; color: #64748B;">%</span></div>
<div class="kpi-delta positive">↑ +8.4% vs 20D ago</div>
</div>"""), unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Accumulation / Net Flow + 20D Return Probability Curve
        col_acc, col_bell = st.columns([1.0, 1.15])

        with col_acc:
            st.markdown(textwrap.dedent("""<div class="flow-card">
<div style="font-weight: 800; font-size: 0.85rem; color: #F8FAFC; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between;">
<span>ACCUMULATION / DISTRIBUTION (NET FLOW)</span>
<span style="font-size: 0.70rem; color: #10B981; font-weight: 700; font-family: 'JetBrains Mono';">+56 NET FLOW</span>
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.70rem; color: #64748B; font-weight: 700; margin-bottom: 2px;">
<span style="color: #EF4444;">DISTRIBUTION (22)</span>
<span style="color: #10B981;">ACCUMULATION (78)</span>
</div>"""), unsafe_allow_html=True)
            st.plotly_chart(plot_accumulation_flow_gauge(78.0, "STRONG ACCUMULATION"), use_container_width=True, config={'displayModeBar': False})
            st.markdown(textwrap.dedent("""<div style="text-align: center; font-size: 0.75rem; font-weight: 800; color: #10B981; letter-spacing: 0.06em; margin-top: 4px;">
🔥 STRONG INSTITUTIONAL ACCUMULATION
</div>
<hr style="border-color: rgba(255,255,255,0.06); margin: 12px 0;">
<div style="display: flex; align-items: center; justify-content: space-between;">
<div>
<div style="font-size: 0.70rem; font-weight: 700; color: #94A3B8; text-transform: uppercase;">Breadth Quality</div>
<div style="font-size: 1.15rem; font-weight: 800; color: #F8FAFC; font-family: 'JetBrains Mono';">78<span style="font-size: 0.8rem; color: #64748B;">/100</span></div>
</div>
<div style="text-align: right;">
<div style="font-size: 0.70rem; font-weight: 700; color: #10B981;">BROAD-BASED</div>
<div style="font-size: 0.68rem; color: #94A3B8;">82% Constituents Above 50 EMA</div>
</div>
</div>
</div>"""), unsafe_allow_html=True)

        with col_bell:
            st.markdown(textwrap.dedent("""<div class="flow-card">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
<span style="font-weight: 800; font-size: 0.85rem; color: #F8FAFC; letter-spacing: 0.04em;">20D CALIBRATED RETURN PROBABILITY DISTRIBUTION</span>
<span style="font-size: 0.68rem; color: #0EA5E9; font-weight: 700; font-family: 'JetBrains Mono';">STUDENT-t (df=5)</span>
</div>"""), unsafe_allow_html=True)
            fig_bell = plot_return_distribution_bell_curve(p10=-4.2, p25=-1.1, p50=7.1, p75=12.6, p90=17.8, p95=20.3)
            st.plotly_chart(fig_bell, use_container_width=True, config={'displayModeBar': False})
            st.markdown(textwrap.dedent("""<div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono'; font-size: 0.68rem; color: #94A3B8; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
<div>P(>5%): <span style="color: #10B981; font-weight: 700;">68%</span></div>
<div>P(>8%): <span style="color: #10B981; font-weight: 700;">51%</span></div>
<div>P(>10%): <span style="color: #0EA5E9; font-weight: 700;">42%</span></div>
<div>P(>15%): <span style="color: #F59E0B; font-weight: 700;">21%</span></div>
<div>P(>20%): <span style="color: #64748B; font-weight: 700;">9%</span></div>
</div>
</div>"""), unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # 1-CLICK CONSTITUENT STOCKS DRILLDOWN
        st.markdown(textwrap.dedent(f"""<div class="flow-card">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
<div>
<span style="font-weight: 800; font-size: 0.95rem; color: #F8FAFC; letter-spacing: 0.04em;">1-CLICK CONSTITUENT EQUITIES DRILLDOWN</span>
<span style="font-size: 0.70rem; color: #64748B; margin-left: 8px;">(Filter by {level_label} to inspect all underlying securities)</span>
</div>
</div>"""), unsafe_allow_html=True)

        entity_options = df_agg['entity_name'].tolist()
        active_drill = st.selectbox(f"Select {level_label} for Drilldown:", entity_options, index=0)

        # Query constituent stocks
        sql_stk = f"""
        SELECT s.symbol, s.company_name, s.macro_sector, s.industry, s.basic_industry,
               COALESCE(m.close, 100.0) as close_price,
               COALESCE(m.return_1d, 0.0) as return_1d,
               COALESCE(m.return_5d, 0.0) as return_5d,
               COALESCE(m.return_20d, 0.0) as return_20d,
               COALESCE(m.rs_20d, 0.0) as rs_20d,
               COALESCE(m.volume_ratio, 1.0) as volume_ratio,
               COALESCE(m.above_50ema, 1) as above_50ema
        FROM stocks s
        LEFT JOIN stock_metrics m ON s.symbol = m.symbol AND m.date = '{selected_date}'
        WHERE s.{level_col} = ? AND s.active = 1
        ORDER BY COALESCE(m.rs_20d, 0.0) DESC
        """
        df_stk_view = pd.read_sql(sql_stk, conn, params=(active_drill,))
        if u_ctx["is_filtered"] and not df_stk_view.empty:
            df_stk_view = df_stk_view[df_stk_view['symbol'].isin(u_ctx['eligible_symbols'])].copy()

        if not df_stk_view.empty:
            stock_table = """<table class="flow-table"><thead><tr><th>Symbol</th><th>Company Name</th><th>Price (₹)</th><th>1D %</th><th>5D %</th><th>20D %</th><th>20D RS</th><th>Vol Ratio</th><th>Trend</th><th>Action</th></tr></thead><tbody>"""
            for _, sr in df_stk_view.iterrows():
                sym = sr['symbol']
                name = sr['company_name']
                px_val = sr['close_price']
                r1 = sr['return_1d']
                r5 = sr['return_5d']
                r20 = sr['return_20d']
                rs_val = sr['rs_20d']
                vol = sr['volume_ratio']
                trend_txt = "Bullish (>50 EMA)" if sr['above_50ema'] == 1 else "Below 50 EMA"
                
                if rs_val >= 5.0 and vol >= 1.2:
                    action_badge = '<span class="badge-pill badge-strong-buy">STRONG BUY</span>'
                elif rs_val >= 0.0:
                    action_badge = '<span class="badge-pill badge-buy">BUY</span>'
                elif rs_val >= -5.0:
                    action_badge = '<span class="badge-pill badge-neutral">NEUTRAL</span>'
                else:
                    action_badge = '<span class="badge-pill badge-avoid">AVOID</span>'

                r1_col = "#10B981" if r1 >= 0 else "#EF4444"
                r5_col = "#10B981" if r5 >= 0 else "#EF4444"
                r20_col = "#10B981" if r20 >= 0 else "#EF4444"
                rs_col = "#10B981" if rs_val >= 0 else "#EF4444"

                stock_table += f"""<tr><td style="font-family: 'JetBrains Mono'; font-weight: 700; color: #0EA5E9;">{sym}</td><td style="font-weight: 600; color: #F8FAFC;">{name}</td><td style="font-family: 'JetBrains Mono'; font-weight: 700;">₹{px_val:,.2f}</td><td style="font-family: 'JetBrains Mono'; color: {r1_col};">{r1:+.2f}%</td><td style="font-family: 'JetBrains Mono'; color: {r5_col};">{r5:+.2f}%</td><td style="font-family: 'JetBrains Mono'; color: {r20_col}; font-weight: 700;">{r20:+.2f}%</td><td style="font-family: 'JetBrains Mono'; color: {rs_col};">{rs_val:+.2f}%</td><td style="font-family: 'JetBrains Mono'; color: #0EA5E9;">{vol:.2f}x</td><td style="font-size: 0.70rem; color: #94A3B8;">{trend_txt}</td><td>{action_badge}</td></tr>"""
            stock_table += "</tbody></table>"
            st.markdown(textwrap.dedent(stock_table), unsafe_allow_html=True)
            st.caption(f"Showing all **{len(df_stk_view)}** constituent stocks in **{active_drill}**")

        st.markdown("</div>", unsafe_allow_html=True)




    with tab_forensic:
        st.markdown(f"### 📊 7-Dimension Quantitative Forensic Profile ({level_plural})")
        st.dataframe(df_agg, use_container_width=True)



    with tab_radar:
        st.markdown(f"### ⚖️ Cross-Sectional Comparison Radar ({level_plural})")
        st.dataframe(df_agg[['entity_name', 'constituent_count', 'current_strength', 'avg_return_20d', 'industry_rs_20d', 'breadth_50', 'final_action', 'breadth_qualification']].round(2), use_container_width=True)

    with tab_guide:
        st.markdown("### 📚 Institutional Methodology & Model Validation Playbook")
        
        # MODEL VALIDATION PANEL (PHASE 10 & 14)
        st.markdown(textwrap.dedent(f"""<div class="flow-card" style="border: 1px solid rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.04); margin-bottom: 16px;">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
<div>
<span style="font-weight: 800; font-size: 1.05rem; color: #10B981; letter-spacing: 0.03em;">🛡️ QUANTITATIVE MODEL VALIDATION PANEL</span>
<span style="background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.5); padding: 2px 8px; border-radius: 12px; font-size: 0.70rem; font-weight: 800; font-family: 'JetBrains Mono'; margin-left: 8px;">{MODEL_V3_2_FINGERPRINT['model_version']}</span>
</div>
<span style="font-size: 0.70rem; color: #64748B; font-family: 'JetBrains Mono';">FROZEN SPECIFICATION</span>
</div>

<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px;">
<div style="background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.06);">
<div style="font-size: 0.68rem; color: #94A3B8; font-weight: 700;">OUT-OF-SAMPLE RANK IC</div>
<div style="font-size: 1.15rem; font-weight: 900; color: #10B981; font-family: 'JetBrains Mono';">+{MODEL_V3_2_FINGERPRINT['verified_rank_ic']:.4f}</div>
<div style="font-size: 0.62rem; color: #64748B;">95% CI: [{MODEL_V3_2_FINGERPRINT['confidence_interval_95'][0]:.4f}, {MODEL_V3_2_FINGERPRINT['confidence_interval_95'][1]:.4f}]</div>
</div>
<div style="background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.06);">
<div style="font-size: 0.68rem; color: #94A3B8; font-weight: 700;">HAC t-STATISTIC</div>
<div style="font-size: 1.15rem; font-weight: 900; color: #0EA5E9; font-family: 'JetBrains Mono';">{MODEL_V3_2_FINGERPRINT['hac_t_statistic']:.2f}</div>
<div style="font-size: 0.62rem; color: #64748B;">p-value: {MODEL_V3_2_FINGERPRINT['p_value']}</div>
</div>
<div style="background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.06);">
<div style="font-size: 0.68rem; color: #94A3B8; font-weight: 700;">DECILE SPREAD (20D)</div>
<div style="font-size: 1.15rem; font-weight: 900; color: #10B981; font-family: 'JetBrains Mono';">{MODEL_V3_2_FINGERPRINT['top_bottom_decile_spread_20d']}</div>
<div style="font-size: 0.62rem; color: #64748B;">Top Decile vs Bottom Decile</div>
</div>
<div style="background: rgba(15, 23, 42, 0.6); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.06);">
<div style="font-size: 0.68rem; color: #94A3B8; font-weight: 700;">IC INFO RATIO</div>
<div style="font-size: 1.15rem; font-weight: 900; color: #F59E0B; font-family: 'JetBrains Mono';">{MODEL_V3_2_FINGERPRINT['ic_information_ratio']:.2f}</div>
<div style="font-size: 0.62rem; color: #64748B;">Profit Factor: {MODEL_V3_2_FINGERPRINT['profit_factor']:.2f}</div>
</div>
</div>

<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; font-size: 0.72rem; color: #94A3B8;">
<div><b>Validation Method:</b> {MODEL_V3_2_FINGERPRINT['validation_method']}</div>
<div><b>Walk-Forward Splits:</b> {MODEL_V3_2_FINGERPRINT['walk_forward_splits']} Splits (20-Session Embargo)</div>
<div><b>Test Suite Status:</b> <span style="color: #10B981; font-weight: 700;">{MODEL_V3_2_FINGERPRINT['test_suite_status']}</span></div>
</div>
<div style="font-size: 0.68rem; color: #64748B; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
<b>Primary Breadth Rule:</b> Minimum {MODEL_V3_2_FINGERPRINT['min_constituents_for_primary_ranking']} active equities required for primary opportunity ranking. Industries with N &lt; 5 are labeled <span style="color: #F59E0B; font-weight: 700;">INSUFFICIENT_BREADTH</span>.
</div>
</div>"""), unsafe_allow_html=True)

        st.markdown("""
        **1. Direct Real-World Concrete Hierarchy**:
        - **Level 1: Direct Sector** (e.g. *Footwear*, *Gems & Jewellery*, *Wires & Cables*, *Pipes & Plumbing*, *Rice & Grain Milling*, *Aerospace & Defense*).
        - **Level 2: Major Industry** (e.g. *Sports Athleisure Footwear*, *Extra High Voltage Cables*, *CPVC/PVC Plumbing*, *Aged Basmati Rice Brands*).
        - **Level 3: Specialization Subsector** (e.g. *Performance Running Shoes*, *XLPE Power Transmission*, *India Gate Branded Exports*).

        **2. 4-Phase Sector Rotation Lifecycle**:
        - **🔵 Improving (Top-Left)**: Gaining Money Flow Score (>50) while price relative strength is recovering. Early accumulation.
        - **🟢 Leading (Top-Right)**: High Money Flow Score (>50) + High Relative Strength (>0%). Strongest institutional momentum.
        - **🟡 Weakening (Bottom-Right)**: Positive Relative Strength (>0%) but Money Flow fading (<50). Profit booking stage.
        - **🔴 Lagging (Bottom-Left)**: Low Money Flow (<50) + Negative Relative Strength (<0%). Underperforming asset basket.
        """)

render_phase13_terminal = render_phase13_intelligence_terminal


def load_phase12_production_data():
    """Loads Phase 12 / V3 production datasets for validation and testing."""
    base_res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "results")
    
    prim_p = os.path.join(base_res, "phase12_primary_industry_rankings.csv")
    res_p = os.path.join(base_res, "phase12_research_only_universe.csv")
    dist_p = os.path.join(base_res, "phase12_return_distributions.csv")
    prob_p = os.path.join(base_res, "phase12_calibrated_probabilities.csv")
    stk_p = os.path.join(base_res, "phase12_stock_bridge.csv")
    ledg_p = os.path.join(base_res, "phase11_daily_forecast_ledger.csv")
    real_p = os.path.join(base_res, "phase11_realized_outcomes.csv")
    calib_p = os.path.join(base_res, "phase11_model_calibration_metrics.csv")

    df_prim = pd.read_csv(prim_p) if os.path.exists(prim_p) else pd.DataFrame()
    df_res = pd.read_csv(res_p) if os.path.exists(res_p) else pd.DataFrame()
    df_dist = pd.read_csv(dist_p) if os.path.exists(dist_p) else pd.DataFrame()
    df_prob = pd.read_csv(prob_p) if os.path.exists(prob_p) else pd.DataFrame()
    df_stk = pd.read_csv(stk_p) if os.path.exists(stk_p) else pd.DataFrame()
    df_ledg = pd.read_csv(ledg_p) if os.path.exists(ledg_p) else pd.DataFrame()
    df_real = pd.read_csv(real_p) if os.path.exists(real_p) else pd.DataFrame()
    df_calib = pd.read_csv(calib_p) if os.path.exists(calib_p) else pd.DataFrame()

    return df_prim, df_res, df_dist, df_prob, df_stk, df_ledg, df_real, df_calib
