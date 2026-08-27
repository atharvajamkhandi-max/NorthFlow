"""
Market Overview Intelligence & Regime Synthesis Page.
Integrated with the Universal Global Hierarchy & Aggregation Lens.
Phase 76: Institutional UI/UX Upgrade — Two-Mode Industry Position & Stock Recommender.
"""

import streamlit as st
import pandas as pd
import numpy as np
import textwrap
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, Any, List

from database.db import Database
from dashboard.components.topbar import render_topbar
from dashboard.components.global_state import get_hierarchy_metadata, render_hierarchy_badge_inline
from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence
from dashboard.components.analytical_card import render_analytical_card
from dashboard.components.theme import get_theme_tokens, get_theme_mode
from analytics.canonical_v3_2_service import get_canonical_stock_quant_score

def render_overview(db: Database, selected_date: str):
    t = get_theme_tokens()
    meta = get_hierarchy_metadata()
    level_label = meta["label"]
    level_plural = meta["plural"]
    level_col = meta["col"]
    badge_html = render_hierarchy_badge_inline()

    # --- TOPBAR & UNIVERSE STATUS ---
    render_topbar(selected_date, page_title="Market Overview Intelligence")

    from dashboard.components.universe_service import get_current_universe_context, render_universe_status_chip
    u_ctx = get_current_universe_context(selected_date)
    render_universe_status_chip(u_ctx)

    # --- ACTIVE UNIVERSE DATA FETCHING ---
    eligible_syms = u_ctx["eligible_symbols_tuple"] if u_ctx["is_filtered"] else None
    df_data, market_meta = get_aggregated_hierarchy_intelligence(selected_date, hierarchy_level_key=None, eligible_symbols=eligible_syms)

    # --- EMPTY UNIVERSE HARD STOP ---
    if u_ctx["is_filtered"] and u_ctx["eligible_count"] == 0:
        st.info(f"🌐 No eligible equities found in the active market universe ({u_ctx['chip_label']}) for session {selected_date}.")
        return

    if df_data.empty:
        st.warning(f"No metric data available for session {selected_date}.")
        return

    regime = market_meta.get("market_regime", "SIDEWAYS")
    regime_mult = market_meta.get("regime_multiplier", 1.0)

    regime_colors = {
        "STRONG_BULL": t["positive"],
        "WEAK_BULL": t["accent"],
        "SIDEWAYS": t["warning"],
        "WEAK_BEAR": "#F97316",
        "STRONG_BEAR": t["negative"]
    }
    regime_color = regime_colors.get(regime, t["accent"])

    strong_buy_cnt = (df_data['final_action'] == 'STRONG BUY').sum() if 'final_action' in df_data.columns else 0
    buy_cnt = (df_data['final_action'] == 'BUY').sum() if 'final_action' in df_data.columns else 0
    watch_cnt = (df_data['final_action'] == 'WATCH').sum() if 'final_action' in df_data.columns else 0
    neutral_cnt = (df_data['final_action'] == 'NEUTRAL').sum() if 'final_action' in df_data.columns else 0
    reduce_cnt = (df_data['final_action'] == 'REDUCE').sum() if 'final_action' in df_data.columns else 0
    avoid_cnt = (df_data['final_action'] == 'AVOID').sum() if 'final_action' in df_data.columns else 0

    # --- MARKET REGIME HERO PANEL ---
    hero_html = f"""<div style="background-color: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 14px 20px; margin-bottom: 16px;">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
<div>
<div style="display: flex; align-items: center; gap: 10px;">
<div style="font-size: 0.70rem; font-weight: 700; color: {t['text_dim']}; text-transform: uppercase; letter-spacing: 0.06em;">MARKET REGIME SYNTHESIS</div>
<span style="background-color: {t['secondary_bg']}; color: {t['accent']}; border: 1px solid {t['card_border']}; padding: 2px 8px; border-radius: 4px; font-size: 0.68rem; font-weight: 700; font-family: 'JetBrains Mono';">ACTIVE: {len(df_data)} {level_plural.upper()}</span>
{badge_html}
</div>
<div style="display: flex; align-items: center; gap: 14px; margin-top: 4px;">
<span style="font-size: 1.5rem; font-weight: 800; color: {regime_color}; letter-spacing: -0.02em;">
{regime}
</span>
<span style="background-color: {t['secondary_bg']}; color: {t['text_muted']}; border: 1px solid {t['card_border']}; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.80rem; font-family: 'JetBrains Mono';">
Multiplier: <b style="color: {regime_color};">{regime_mult:.2f}x</b>
</span>
</div>
</div>
<div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
<div style="text-align: right; background-color: {t['secondary_bg']}; border: 1px solid {t['card_border']}; padding: 5px 10px; border-radius: 6px;">
<div style="font-size: 0.62rem; color: {t['text_dim']}; font-weight: 700;">STRONG BUY / BUY</div>
<div style="font-size: 1.05rem; font-weight: 800; color: {t['positive']}; font-family: 'JetBrains Mono', monospace;">{strong_buy_cnt + buy_cnt} <span style="font-size: 0.68rem; color: {t['text_dim']};">/ {len(df_data)}</span></div>
</div>
<div style="text-align: right; background-color: {t['secondary_bg']}; border: 1px solid {t['card_border']}; padding: 5px 10px; border-radius: 6px;">
<div style="font-size: 0.62rem; color: {t['text_dim']}; font-weight: 700;">WATCH / NEUTRAL</div>
<div style="font-size: 1.05rem; font-weight: 800; color: {t['warning']}; font-family: 'JetBrains Mono', monospace;">{watch_cnt + neutral_cnt} <span style="font-size: 0.68rem; color: {t['text_dim']};">/ {len(df_data)}</span></div>
</div>
<div style="text-align: right; background-color: {t['secondary_bg']}; border: 1px solid {t['card_border']}; padding: 5px 10px; border-radius: 6px;">
<div style="font-size: 0.62rem; color: {t['text_dim']}; font-weight: 700;">REDUCE / AVOID</div>
<div style="font-size: 1.05rem; font-weight: 800; color: {t['negative']}; font-family: 'JetBrains Mono', monospace;">{reduce_cnt + avoid_cnt} <span style="font-size: 0.68rem; color: {t['text_dim']};">/ {len(df_data)}</span></div>
</div>
</div>
</div>
</div>"""
    st.markdown(textwrap.dedent(hero_html).strip(), unsafe_allow_html=True)

    # --- TWO-MODE SEGMENTED CONTROL ---
    if "overview_mode" not in st.session_state:
        st.session_state["overview_mode"] = "INDUSTRY POSITION"

    mode_options = ["🏢 INDUSTRY POSITION", "📈 STOCK RECOMMENDER"]
    mode_index = 0 if st.session_state["overview_mode"] == "INDUSTRY POSITION" else 1

    m_col1, m_col2 = st.columns([3.5, 1.5])
    with m_col1:
        sel_mode = st.radio(
            "Select Analytical Mode",
            mode_options,
            index=mode_index,
            horizontal=True,
            key="overview_mode_selector",
            label_visibility="collapsed"
        )
        if "INDUSTRY" in sel_mode:
            st.session_state["overview_mode"] = "INDUSTRY POSITION"
        else:
            st.session_state["overview_mode"] = "STOCK RECOMMENDER"

    st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # MODE A: INDUSTRY POSITION
    # =========================================================================
    if st.session_state["overview_mode"] == "INDUSTRY POSITION":
        # Control Bar
        c_r1, c_r2, c_r3 = st.columns([1.5, 1.2, 2.3])
        with c_r1:
            ind_rank_by = st.selectbox(
                "Rank By",
                ["Current Strength", "20D Expected Return", "Breadth 50", "Relative Strength 20D", "Flow Acceleration"],
                index=0,
                key="overview_ind_rank_by"
            )
        with c_r2:
            ind_shown = st.selectbox(
                "Industries Shown",
                [10, 20, 30, 50, "ALL"],
                index=1,
                key="overview_ind_shown"
            )
        with c_r3:
            all_entities = sorted(df_data['entity_name'].dropna().unique().tolist())
            curr_sel_ind = st.session_state.get("overview_selected_industry", all_entities[0] if all_entities else "")
            if curr_sel_ind not in all_entities and all_entities:
                curr_sel_ind = all_entities[0]
            sel_ind_dropdown = st.selectbox(
                f"Inspect {level_label} Drilldown",
                all_entities,
                index=all_entities.index(curr_sel_ind) if curr_sel_ind in all_entities else 0,
                key="overview_ind_dropdown"
            )
            if sel_ind_dropdown != st.session_state.get("overview_selected_industry"):
                st.session_state["overview_selected_industry"] = sel_ind_dropdown

        active_drill_entity = st.session_state.get("overview_selected_industry", sel_ind_dropdown)

        # Sort industries according to selected ranking dimension
        df_ind_sorted = df_data.copy()
        if ind_rank_by == "Current Strength":
            df_ind_sorted = df_ind_sorted.sort_values('current_strength', ascending=False)
        elif ind_rank_by == "20D Expected Return":
            df_ind_sorted = df_ind_sorted.sort_values('exp_return_20d', ascending=False)
        elif ind_rank_by == "Breadth 50":
            df_ind_sorted = df_ind_sorted.sort_values('breadth_50', ascending=False)
        elif ind_rank_by == "Relative Strength 20D":
            df_ind_sorted = df_ind_sorted.sort_values('industry_rs_20d', ascending=False)
        elif ind_rank_by == "Flow Acceleration":
            df_ind_sorted = df_ind_sorted.sort_values('score_change_5d', ascending=False)

        df_ind_sorted = df_ind_sorted.reset_index(drop=True)
        df_ind_sorted['Rank'] = np.arange(1, len(df_ind_sorted) + 1)

        # Slice display count (presentation only)
        if ind_shown != "ALL":
            df_display_cards = df_ind_sorted.head(int(ind_shown))
        else:
            df_display_cards = df_ind_sorted

        # Section Header
        st.markdown(f"""
        <div style="margin: 12px 0 8px 0; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.05rem; font-weight: 800; color: {t['text_primary']};">
                    🏆 Ranked {level_plural} ({ind_rank_by})
                </span>
                <span style="font-size: 0.75rem; color: {t['text_muted']}; margin-left: 8px;">
                    Showing {len(df_display_cards)} of {len(df_ind_sorted)} active universe entities · Click card or select dropdown to drill down
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Two-Column Card Grid with Selection Buttons
        grid_c1, grid_c2 = st.columns(2)
        grid_cols = [grid_c1, grid_c2]

        for idx, row in df_display_cards.iterrows():
            target_col = grid_cols[idx % 2]
            ent_name = str(row.get("entity_name", "Entity"))
            sector_name = str(row.get("macro_sector", ""))
            rank_num = int(row.get("Rank", idx + 1))
            action_val = str(row.get("final_action", "WATCH"))
            trend_val = str(row.get("trend_rating", "NEUTRAL"))
            strength_val = float(row.get("current_strength", 50.0))
            exp_ret_val = float(row.get("exp_return_20d", 0.0))
            breadth_val = float(row.get("breadth_50", 50.0))
            stocks_cnt = int(row.get("constituent_count", 0))
            conf_val = float(row.get("confidence_score", 50.0))
            risk_val = float(row.get("risk_score", 50.0))

            is_active_sel = (ent_name == active_drill_entity)

            card_html = render_analytical_card(
                rank=rank_num,
                title=ent_name,
                subtitle=sector_name,
                action=action_val,
                trend=trend_val,
                strength=strength_val,
                exp_return_20d=exp_ret_val,
                confidence=conf_val,
                risk=risk_val,
                breadth_50=breadth_val,
                constituent_count=stocks_cnt,
                extra_metric_label="CONF / RISK",
                extra_metric_value=f"{conf_val:.0f} / {risk_val:.0f}",
                is_selected=is_active_sel
            )

            with target_col:
                st.markdown(card_html, unsafe_allow_html=True)
                btn_label = f"✓ {ent_name} (Active Drilldown)" if is_active_sel else f"⚡ Inspect {ent_name} ➜"
                btn_type = "primary" if is_active_sel else "secondary"
                if st.button(btn_label, key=f"ov_ind_card_btn_{idx}_{ent_name}", type=btn_type, use_container_width=True):
                    st.session_state["overview_selected_industry"] = ent_name
                    st.rerun()

        # --- CONSTITUENT DRILLDOWN PANEL ---
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        st.divider()

        st.markdown(f"""
        <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <span style="font-size: 1.15rem; font-weight: 800; color: {t['text_primary']};">
                    🔍 {active_drill_entity} — Active Universe Constituents
                </span>
                <div style="font-size: 0.78rem; color: {t['text_muted']}; margin-top: 2px;">
                    Filtered strictly by active universe (<b style="color: {t['accent']};">{u_ctx['chip_label']}</b>). Zero truncation.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Query constituent stocks with active universe bounding
        conn = db.get_connection()
        if u_ctx["is_filtered"]:
            if u_ctx["eligible_symbols"]:
                sym_list = list(u_ctx["eligible_symbols"])
                ph = ",".join(["?"] * len(sym_list))
                sql_stk = f"""
                SELECT s.symbol, s.company_name, s.macro_sector, s.industry, s.basic_industry, s.series, s.sme_status,
                       COALESCE(scm.market_cap, 100.0) as market_cap_cr,
                       COALESCE(m.close, 100.0) as close_price,
                       COALESCE(m.return_1d, 0.0) as return_1d,
                       COALESCE(m.return_5d, 0.0) as return_5d,
                       COALESCE(m.return_20d, 0.0) as return_20d,
                       COALESCE(m.rs_20d, 0.0) as rs_20d,
                       COALESCE(m.volume_ratio, 1.0) as volume_ratio,
                       COALESCE(m.above_50ema, 0) as above_50ema
                FROM stocks s
                LEFT JOIN stock_classification_master_v3 scm ON s.symbol = scm.symbol
                LEFT JOIN stock_metrics m ON s.symbol = m.symbol AND m.date = ?
                WHERE s.{level_col} = ? AND s.active = 1 AND s.symbol IN ({ph})
                ORDER BY COALESCE(m.rs_20d, 0.0) DESC
                """
                df_drill_stk = pd.read_sql(sql_stk, conn, params=[selected_date, active_drill_entity] + sym_list)
            else:
                df_drill_stk = pd.DataFrame()
        else:
            sql_stk = f"""
            SELECT s.symbol, s.company_name, s.macro_sector, s.industry, s.basic_industry, s.series, s.sme_status,
                   COALESCE(scm.market_cap, 100.0) as market_cap_cr,
                   COALESCE(m.close, 100.0) as close_price,
                   COALESCE(m.return_1d, 0.0) as return_1d,
                   COALESCE(m.return_5d, 0.0) as return_5d,
                   COALESCE(m.return_20d, 0.0) as return_20d,
                   COALESCE(m.rs_20d, 0.0) as rs_20d,
                   COALESCE(m.volume_ratio, 1.0) as volume_ratio,
                   COALESCE(m.above_50ema, 0) as above_50ema
            FROM stocks s
            LEFT JOIN stock_classification_master_v3 scm ON s.symbol = scm.symbol
            LEFT JOIN stock_metrics m ON s.symbol = m.symbol AND m.date = ?
            WHERE s.{level_col} = ? AND s.active = 1
            ORDER BY COALESCE(m.rs_20d, 0.0) DESC
            """
            df_drill_stk = pd.read_sql(sql_stk, conn, params=[selected_date, active_drill_entity])

        if not df_drill_stk.empty:
            df_drill_disp = df_drill_stk.copy()
            df_drill_disp['market_cap_disp'] = df_drill_disp['market_cap_cr'].apply(lambda x: f"₹{x:,.0f} Cr")
            df_drill_disp['close_disp'] = df_drill_disp['close_price'].apply(lambda x: f"₹{x:,.2f}")
            df_drill_disp['ret_1d_disp'] = df_drill_disp['return_1d'].apply(lambda x: f"{'+' if x>0 else ''}{x:.2f}%")
            df_drill_disp['ret_5d_disp'] = df_drill_disp['return_5d'].apply(lambda x: f"{'+' if x>0 else ''}{x:.2f}%")
            df_drill_disp['ret_20d_disp'] = df_drill_disp['return_20d'].apply(lambda x: f"{'+' if x>0 else ''}{x:.2f}%")
            df_drill_disp['rs_20d_disp'] = df_drill_disp['rs_20d'].apply(lambda x: f"{'+' if x>0 else ''}{x:.1f}")
            df_drill_disp['vol_disp'] = df_drill_disp['volume_ratio'].apply(lambda x: f"{x:.2f}x")
            df_drill_disp['trend_disp'] = df_drill_disp['above_50ema'].apply(lambda x: "Bullish (Above 50E)" if x == 1 else "Bearish (Below 50E)")

            table_df = df_drill_disp[[
                'symbol', 'company_name', 'market_cap_disp', 'close_disp',
                'ret_1d_disp', 'ret_5d_disp', 'ret_20d_disp', 'rs_20d_disp',
                'vol_disp', 'trend_disp', 'sme_status'
            ]].rename(columns={
                'symbol': 'Symbol',
                'company_name': 'Company Name',
                'market_cap_disp': 'Market Cap',
                'close_disp': 'Price',
                'ret_1d_disp': '1D %',
                'ret_5d_disp': '5D %',
                'ret_20d_disp': '20D %',
                'rs_20d_disp': '20D RS',
                'vol_disp': 'Vol Ratio',
                'trend_disp': 'Trend (50 EMA)',
                'sme_status': 'SME Status'
            })
            st.dataframe(table_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"No eligible constituents found for '{active_drill_entity}' under current active market universe filter.")

    # =========================================================================
    # MODE B: STOCK RECOMMENDER
    # =========================================================================
    else:
        # Stock Recommender Controls
        s_c1, s_c2, s_c3 = st.columns([1.5, 1.2, 2.3])
        with s_c1:
            stock_rank_by = st.selectbox(
                "Rank By",
                ["Model Quant Score", "20D Expected Return", "Relative Strength 20D", "5D Momentum", "Volume Momentum"],
                index=0,
                key="overview_stock_rank_by"
            )
        with s_c2:
            stocks_shown = st.selectbox(
                "Stocks Shown",
                [10, 20, 30, 50],
                index=1,
                key="overview_stocks_shown"
            )
        with s_c3:
            action_filter = st.selectbox(
                "Filter by Model Action",
                ["All Model Actions", "STRONG BUY", "BUY", "WATCH", "NEUTRAL", "REDUCE", "AVOID"],
                index=0,
                key="overview_stock_action_filter"
            )

        # Retrieve canonical stock quant score
        df_stocks_raw = get_canonical_stock_quant_score(selected_date)

        # STRICT ACTIVE UNIVERSE BOUNDING BEFORE RANKING
        if u_ctx["is_filtered"]:
            if not df_stocks_raw.empty and u_ctx["eligible_symbols"]:
                df_stocks_filtered = df_stocks_raw[df_stocks_raw['symbol'].isin(u_ctx["eligible_symbols"])].copy()
            else:
                df_stocks_filtered = pd.DataFrame()
        else:
            df_stocks_filtered = df_stocks_raw.copy()

        if df_stocks_filtered.empty:
            st.info(f"No eligible stocks found for active universe ({u_ctx['chip_label']}) on session {selected_date}.")
            return

        # Add Market Cap from classification master
        with db.get_connection() as conn:
            df_mcap = pd.read_sql("SELECT symbol, market_cap FROM stock_classification_master_v3", conn)
        df_stocks_filtered = pd.merge(df_stocks_filtered, df_mcap, on='symbol', how='left')
        df_stocks_filtered['market_cap'] = df_stocks_filtered['market_cap'].fillna(100.0)

        # Filter by Action if specified
        if action_filter != "All Model Actions":
            df_stocks_filtered = df_stocks_filtered[df_stocks_filtered['final_action'] == action_filter]

        # Sorting logic
        if stock_rank_by == "Model Quant Score":
            df_stocks_sorted = df_stocks_filtered.sort_values('stock_strength_score', ascending=False)
        elif stock_rank_by == "20D Expected Return":
            df_stocks_sorted = df_stocks_filtered.sort_values('return_20d', ascending=False)
        elif stock_rank_by == "Relative Strength 20D":
            df_stocks_sorted = df_stocks_filtered.sort_values('rs_20d', ascending=False)
        elif stock_rank_by == "5D Momentum":
            df_stocks_sorted = df_stocks_filtered.sort_values('return_5d', ascending=False)
        elif stock_rank_by == "Volume Momentum":
            df_stocks_sorted = df_stocks_filtered.sort_values('volume_ratio', ascending=False)
        else:
            df_stocks_sorted = df_stocks_filtered.sort_values('stock_strength_score', ascending=False)

        df_stocks_sorted = df_stocks_sorted.reset_index(drop=True)
        df_stocks_sorted['Rank'] = np.arange(1, len(df_stocks_sorted) + 1)
        df_stocks_display = df_stocks_sorted.head(int(stocks_shown))

        # Section Title
        st.markdown(f"""
        <div style="margin: 12px 0 8px 0;">
            <span style="font-size: 1.05rem; font-weight: 800; color: {t['text_primary']};">
                🎯 Top Recommended Equities ({stock_rank_by})
            </span>
            <span style="font-size: 0.75rem; color: {t['text_muted']}; margin-left: 8px;">
                Showing top {len(df_stocks_display)} of {len(df_stocks_filtered)} active universe equities
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Render Stock Cards in 2-Column Responsive Grid
        s_grid1, s_grid2 = st.columns(2)
        s_cols = [s_grid1, s_grid2]

        for s_idx, s_row in df_stocks_display.iterrows():
            target_s_col = s_cols[s_idx % 2]
            sym = str(s_row.get("symbol", ""))
            c_name = str(s_row.get("company_name", sym))
            sec = str(s_row.get("macro_sector", ""))
            ind = str(s_row.get("industry", ""))
            r_num = int(s_row.get("Rank", s_idx + 1))
            action_s = str(s_row.get("final_action", "WATCH"))
            score_s = float(s_row.get("stock_strength_score", 50.0))
            px_val = float(s_row.get("close_price", 100.0))
            r5_val = float(s_row.get("return_5d", 0.0))
            r20_val = float(s_row.get("return_20d", 0.0))
            rs20_val = float(s_row.get("rs_20d", 0.0))
            vol_val = float(s_row.get("volume_ratio", 1.0))
            mc_val = float(s_row.get("market_cap", 100.0))

            card_s_html = render_analytical_card(
                rank=r_num,
                title=f"{sym} — {c_name}",
                subtitle=f"{sec} · {ind} · ₹{mc_val:,.0f} Cr",
                action=action_s,
                trend=f"Vol: {vol_val:.1f}x · 5D: {'+' if r5_val>0 else ''}{r5_val:.1f}%",
                strength=score_s,
                exp_return_20d=r20_val,
                confidence=score_s,
                risk=100.0 - score_s,
                breadth_50=100.0 if s_row.get("above_50ema") == 1 else 0.0,
                constituent_count=0,
                extra_metric_label="20D RS",
                extra_metric_value=f"{'+' if rs20_val>0 else ''}{rs20_val:.1f}"
            )

            with target_s_col:
                st.markdown(card_s_html, unsafe_allow_html=True)

        # Full Tabular Recommender View
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        st.markdown(f"#### 📋 Full Model Recommender Roster ({len(df_stocks_filtered)} Active Equities)")

        df_table_stk = df_stocks_filtered.sort_values('stock_strength_score', ascending=False).reset_index(drop=True)
        df_table_stk['Rank'] = np.arange(1, len(df_table_stk) + 1)
        df_table_stk['market_cap_disp'] = df_table_stk['market_cap'].apply(lambda x: f"₹{x:,.0f} Cr")
        df_table_stk['close_disp'] = df_table_stk['close_price'].apply(lambda x: f"₹{x:,.2f}")
        df_table_stk['score_disp'] = df_table_stk['stock_strength_score'].apply(lambda x: f"{x:.1f}/100")
        df_table_stk['ret_5d_disp'] = df_table_stk['return_5d'].apply(lambda x: f"{'+' if x>0 else ''}{x:.2f}%")
        df_table_stk['ret_20d_disp'] = df_table_stk['return_20d'].apply(lambda x: f"{'+' if x>0 else ''}{x:.2f}%")
        df_table_stk['rs_20d_disp'] = df_table_stk['rs_20d'].apply(lambda x: f"{'+' if x>0 else ''}{x:.1f}")
        df_table_stk['vol_disp'] = df_table_stk['volume_ratio'].apply(lambda x: f"{x:.2f}x")

        table_stock_view = df_table_stk[[
            'Rank', 'symbol', 'company_name', 'industry', 'market_cap_disp',
            'close_disp', 'score_disp', 'final_action', 'ret_5d_disp',
            'ret_20d_disp', 'rs_20d_disp', 'vol_disp'
        ]].rename(columns={
            'symbol': 'Symbol',
            'company_name': 'Company Name',
            'industry': 'Major Industry',
            'market_cap_disp': 'Market Cap',
            'close_disp': 'Price',
            'score_disp': 'Quant Score',
            'final_action': 'Model Action',
            'ret_5d_disp': '5D %',
            'ret_20d_disp': '20D %',
            'rs_20d_disp': '20D RS',
            'vol_disp': 'Vol Ratio'
        })
        st.dataframe(table_stock_view, use_container_width=True, hide_index=True)

