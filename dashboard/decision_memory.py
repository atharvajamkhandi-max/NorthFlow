"""
dashboard/decision_memory.py
Dedicated, Isolated, Layman-Friendly Historical Decision Memory UI.
Phase 33B: Honest Gap Visualization, Accurate Field Applicability, Clean Hover Markers,
and Read-Only Model-Implied Projections.
Strictly Read-Only. Never alters model parameters, weights, or database records.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from storage.decision_ledger_query_service import DecisionLedgerQueryService
from storage.dynamic_retention_service import DynamicRetentionService
from storage.canonical_forecast_service import CanonicalForecastService

def _get_rating_badge(rating: str) -> str:
    """Returns clean HTML badge with layman-friendly colors."""
    rating_clean = str(rating or "NEUTRAL").upper()
    color_map = {
        "STRONG_BUY": ("#059669", "#ECFDF5", "⭐ STRONG BUY"),
        "BUY": ("#10B981", "#ECFDF5", "▲ BUY"),
        "WATCH": ("#3B82F6", "#EFF6FF", "👁 WATCH"),
        "NEUTRAL": ("#64748B", "#F3F4F6", "■ NEUTRAL"),
        "REDUCE": ("#F59E0B", "#FFFBEB", "▼ REDUCE"),
        "AVOID": ("#EF4444", "#FEF2F2", "✖ AVOID"),
    }
    border, bg, label = color_map.get(rating_clean, ("#6B7280", "#1E2638", rating_clean))
    return f"""<span style="background-color: #111622; color: {border}; border: 1px solid {border}; border-radius: 4px; padding: 2px 8px; font-weight: 700; font-size: 0.82rem; letter-spacing: 0.04em;">{label}</span>"""

def _get_flow_badge(flow: Optional[str], entity_type: str = "STOCK") -> str:
    """Returns entity-appropriate flow state badge."""
    if entity_type == "STOCK":
        return "<span style='color: #64748B; font-size: 0.78rem;'>Not applicable at stock level</span>"
    if not flow or str(flow).upper() in ("NONE", "NAN", "NULL", ""):
        return "<span style='color: #64748B;'>—</span>"
    flow_clean = str(flow).upper()
    if "ACCUMULATION" in flow_clean:
        return "<span style='color: #10B981; font-weight: 700;'>🟢 ACCUMULATION</span>"
    elif "DISTRIBUTION" in flow_clean:
        return "<span style='color: #EF4444; font-weight: 700;'>🔴 DISTRIBUTION</span>"
    return "<span style='color: #94A3B8; font-weight: 600;'>⚪ NEUTRAL</span>"

def _get_radar_badge(radar_val: Optional[float], alert_level: Optional[str], entity_type: str = "STOCK") -> Tuple[str, str]:
    """Returns entity-appropriate early radar display."""
    if entity_type == "STOCK":
        return "Not applicable at stock level", "#64748B"
    if radar_val is None or pd.isna(radar_val):
        return "Normal (—)", "#94A3B8"
    
    alert = str(alert_level or "NORMAL").upper()
    color = "#10B981" if alert == "HIGH" else ("#F59E0B" if alert == "MEDIUM" else "#94A3B8")
    return f"{alert} ({radar_val:.1f})", color

def render_decision_memory_ui(db=None, selected_date: Optional[str] = None):
    """
    Renders the dedicated Historical Decision Memory UI.
    Lazy-loads entity history on demand with sub-15ms response times.
    """
    st.markdown("""
    <div style="padding: 4px 0 16px 0;">
        <h2 style="margin: 0; font-size: 1.45rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.01em;">
            🧠 Historical Decision Memory & Projections
        </h2>
        <p style="margin: 3px 0 0 0; color: #94A3B8; font-size: 0.85rem;">
            Immutable point-in-time record of quantitative model decisions with honest gap rendering & canonical projections.
        </p>
    </div>
    """, unsafe_allow_html=True)

    query_svc = DecisionLedgerQueryService()
    forecast_svc = CanonicalForecastService()

    # 1. ENTITY SELECTOR CONTROLS
    col_type, col_entity, col_range = st.columns([1.2, 2.8, 1.5])

    with col_type:
        entity_type = st.selectbox(
            "Select Entity Level",
            options=["STOCK", "INDUSTRY", "SECTOR"],
            index=0,
            key="hdm_entity_type"
        )

    with col_entity:
        if entity_type == "STOCK":
            selected_entity = st.text_input("Enter Stock Symbol", value="RELIANCE", key="hdm_entity_input").strip().upper()
        elif entity_type == "INDUSTRY":
            selected_entity = st.text_input("Enter Industry Name", value="Stainless Steels", key="hdm_entity_input").strip()
        else:
            selected_entity = st.text_input("Enter Sector Name", value="Steel", key="hdm_entity_input").strip()

    with col_range:
        period_choice = st.selectbox(
            "Historical Range",
            options=["1M", "3M", "6M", "12M", "ALL"],
            index=3,  # 12M default
            key="hdm_period_choice"
        )

    if not selected_entity:
        st.info("💡 Please enter a valid symbol or industry name above to inspect historical memory.")
        return

    # Fetch History (sub-15ms lazy load)
    df_history = query_svc.get_entity_history(
        entity_type=entity_type,
        entity_id=selected_entity,
        period=period_choice
    )

    if df_history.empty:
        st.warning(f"⚠️ No historical decision snapshots found for {entity_type} '{selected_entity}'. Please check spelling or verify entity existence.")
        return

    latest_rec = df_history.iloc[-1]
    curr_date = latest_rec["trade_date"]
    entity_name = str(latest_rec.get("entity_name", selected_entity))
    p_industry = latest_rec.get("parent_industry")
    p_sector = latest_rec.get("parent_sector")
    curr_price = float(latest_rec.get("close_price", 0.0)) if latest_rec.get("close_price") else None

    # Resolve Current Score & View cleanly
    rating_val = str(latest_rec.get("rating_action", "NEUTRAL"))
    raw_score = float(latest_rec.get("score", 0.0))
    
    # Stock score fallback check
    if entity_type == "STOCK":
        if raw_score > 0.0:
            score_display = f"{raw_score:.1f} / 100"
        else:
            # Try live canonical stock service
            try:
                from analytics.canonical_v3_2_service import get_canonical_stock_quant_score
                df_live_stk = get_canonical_stock_quant_score(curr_date, symbol=selected_entity)
                if not df_live_stk.empty and df_live_stk["stock_strength_score"].iloc[0] > 0:
                    live_score = float(df_live_stk["stock_strength_score"].iloc[0])
                    score_display = f"{live_score:.1f} / 100 (Canonical V3.2)"
                else:
                    score_display = "Not Available (Legacy Snapshot)"
            except Exception:
                score_display = "Not Available"
    else:
        score_display = f"{raw_score:.1f} / 100"

    # 2. CURRENT STATE EXECUTIVE SUMMARY
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.markdown(f"""
        <div style="background: #111622; border: 1px solid #1E2638; border-radius: 6px; padding: 10px 14px; min-height: 82px;">
            <div style="font-size: 0.70rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Entity Profile</div>
            <div style="font-size: 1.05rem; font-weight: 800; color: #F8FAFC; margin-top: 2px;">{entity_name}</div>
            <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 2px;">{selected_entity} • {entity_type}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        badge_html = _get_rating_badge(rating_val)
        st.markdown(f"""
        <div style="background: #111622; border: 1px solid #1E2638; border-radius: 6px; padding: 10px 14px; min-height: 82px;">
            <div style="font-size: 0.70rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Latest Model View</div>
            <div style="margin-top: 4px;">{badge_html}</div>
            <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 4px;">Conviction: <b style="color: #F8FAFC;">{score_display}</b></div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        flow_html = _get_flow_badge(latest_rec.get("flow_state"), entity_type=entity_type)
        st.markdown(f"""
        <div style="background: #111622; border: 1px solid #1E2638; border-radius: 6px; padding: 10px 14px; min-height: 82px;">
            <div style="font-size: 0.70rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Institutional Flow</div>
            <div style="margin-top: 4px;">{flow_html}</div>
            <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 4px;">Session: {curr_date}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        radar_text, radar_col = _get_radar_badge(latest_rec.get("early_radar_score"), latest_rec.get("alert_level"), entity_type=entity_type)
        st.markdown(f"""
        <div style="background: #111622; border: 1px solid #1E2638; border-radius: 6px; padding: 10px 14px; min-height: 82px;">
            <div style="font-size: 0.70rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Early Radar Precursor</div>
            <div style="font-size: 0.95rem; font-weight: 800; color: {radar_col}; margin-top: 4px;">{radar_text}</div>
            <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 4px;">Precursor Momentum</div>
        </div>
        """, unsafe_allow_html=True)

    with c5:
        if entity_type == "STOCK":
            p_val = f"₹{curr_price:,.2f}" if curr_price else "—"
            p_lbl = "Reference Close Price"
        else:
            p_val = f"{score_display}"
            p_lbl = "Strength Metric"
        
        p_ctx = f"{p_industry}" if p_industry else (f"{p_sector}" if p_sector else "Taxonomy")
        st.markdown(f"""
        <div style="background: #111622; border: 1px solid #1E2638; border-radius: 6px; padding: 10px 14px; min-height: 82px;">
            <div style="font-size: 0.70rem; font-weight: 700; color: #64748B; text-transform: uppercase;">{p_lbl}</div>
            <div style="font-size: 1.05rem; font-weight: 800; color: #F8FAFC; margin-top: 2px;">{p_val}</div>
            <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 2px;">{p_ctx}</div>
        </div>
        """, unsafe_allow_html=True)

    # 3. HISTORICAL PRICE & DECISION CHART (HONEST GAP HANDLING & CLEAN MARKERS)
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #F8FAFC;'>📈 Historical Trajectory vs Model Decisions</h4>", unsafe_allow_html=True)
    st.caption("Visual audit: Answers 'Did the model upgrade or downgrade its view before or after the price/strength moved?'")

    # Detect date gaps (> 10 calendar days)
    df_chart = df_history.copy()
    df_chart["dt"] = pd.to_datetime(df_chart["trade_date"])
    df_chart["gap_days"] = df_chart["dt"].diff().dt.days
    has_large_gap = (df_chart["gap_days"] > 10).any()

    if has_large_gap:
        gap_row = df_chart[df_chart["gap_days"] > 10].iloc[0]
        st.info(f"ℹ️ **Historical Data Gap Notice**: A non-contiguous gap of {int(gap_row['gap_days'])} days exists between historical sessions. The chart renders actual historical observations with honest visual separation (no artificial connecting lines).")

    has_prices = (entity_type == "STOCK") and df_chart["close_price"].notnull().any()

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.65, 0.35],
        subplot_titles=(
            f"{entity_name} — Price Trajectory & Model Rating Milestones" if has_prices else f"{entity_name} — Historical Strength Trajectory",
            "Model Conviction Score (0-100)" if entity_type != "STOCK" or raw_score > 0 else "Decision Milestones Timeline"
        )
    )

    marker_colors = {
        "STRONG_BUY": "#059669",
        "BUY": "#10B981",
        "WATCH": "#3B82F6",
        "NEUTRAL": "#64748B",
        "REDUCE": "#F59E0B",
        "AVOID": "#EF4444"
    }

    # Split into contiguous segments across gaps (>10 days) so Plotly does NOT draw straight lines
    if has_prices:
        gap_indices = df_chart.index[df_chart["gap_days"] > 10].tolist()
        split_points = [0] + gap_indices + [len(df_chart)]
        
        for i in range(len(split_points) - 1):
            seg = df_chart.iloc[split_points[i]:split_points[i+1]]
            if not seg.empty:
                fig.add_trace(
                    go.Scatter(
                        x=seg["trade_date"],
                        y=seg["close_price"],
                        name="Close Price" if i == 0 else "",
                        showlegend=(i == 0),
                        line=dict(color="#38BDF8", width=2.0),
                        mode="lines",
                        connectgaps=False
                    ),
                    row=1, col=1
                )

        # Overlay rating transition markers (Clean points, NO overlapping permanent text)
        df_chart["prev_rating"] = df_chart["rating_action"].shift(1)
        transitions = df_chart[(df_chart["rating_action"] != df_chart["prev_rating"]) & (df_chart["close_price"].notnull())].copy()

        for rating, group in transitions.groupby("rating_action"):
            mcolor = marker_colors.get(rating, "#94A3B8")
            custom_data = []
            for _, gr in group.iterrows():
                prev_str = str(gr.get("prev_rating") or "None")
                p_str = f"₹{gr['close_price']:,.2f}"
                sc_str = f"{gr['score']:.1f}" if gr['score'] > 0 else "N/A"
                custom_data.append([prev_str, sc_str, p_str])

            fig.add_trace(
                go.Scatter(
                    x=group["trade_date"],
                    y=group["close_price"],
                    mode="markers",
                    name=f"Milestone: {rating}",
                    customdata=custom_data,
                    hovertemplate="<b>Date: %{x}</b><br>New View: " + str(rating) + "<br>Previous View: %{customdata[0]}<br>Score: %{customdata[1]}<br>Price: %{customdata[2]}<extra></extra>",
                    marker=dict(size=9, color=mcolor, symbol="circle", line=dict(width=1.5, color="#FFFFFF"))
                ),
                row=1, col=1
            )
    else:
        # Industry / Sector strength trajectory (segmented by gaps)
        gap_indices = df_chart.index[df_chart["gap_days"] > 10].tolist()
        split_points = [0] + gap_indices + [len(df_chart)]
        for i in range(len(split_points) - 1):
            seg = df_chart.iloc[split_points[i]:split_points[i+1]]
            if not seg.empty:
                fig.add_trace(
                    go.Scatter(
                        x=seg["trade_date"],
                        y=seg["score"],
                        name="Strength Score" if i == 0 else "",
                        showlegend=(i == 0),
                        line=dict(color="#00D084", width=2.5),
                        mode="lines",
                        connectgaps=False
                    ),
                    row=1, col=1
                )

    # Subplot 2: Score Trajectory & Early Radar
    if entity_type != "STOCK" or raw_score > 0:
        fig.add_trace(
            go.Scatter(
                x=df_chart["trade_date"],
                y=df_chart["score"],
                name="Model Score",
                line=dict(color="#10B981", width=2),
                mode="lines",
                connectgaps=False
            ),
            row=2, col=1
        )

        if df_chart["early_radar_score"].notnull().any() and entity_type != "STOCK":
            fig.add_trace(
                go.Scatter(
                    x=df_chart["trade_date"],
                    y=df_chart["early_radar_score"],
                    name="Early Radar",
                    line=dict(color="#F59E0B", width=1.5, dash="dot"),
                    mode="lines",
                    connectgaps=False
                ),
                row=2, col=1
            )
    else:
        # For stocks with legacy placeholder scores, show a clean milestone bar timeline
        fig.add_trace(
            go.Scatter(
                x=df_chart["trade_date"],
                y=[1.0] * len(df_chart),
                name="Active Coverage",
                mode="markers",
                marker=dict(size=4, color="#38BDF8")
            ),
            row=2, col=1
        )

    fig.update_layout(
        template="plotly_dark",
        height=480,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
        hovermode="x unified",
        paper_bgcolor="#0E131F",
        plot_bgcolor="#111622"
    )
    fig.update_xaxes(showgrid=True, gridcolor="#1E2638")
    fig.update_yaxes(showgrid=True, gridcolor="#1E2638")

    st.plotly_chart(fig, use_container_width=True)

    # 4. READ-ONLY CANONICAL PROJECTION / MODEL-IMPLIED OUTLOOK PANEL
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #F8FAFC;'>🔮 Model-Implied Probabilistic Projections (Read-Only)</h4>", unsafe_allow_html=True)
    st.caption("Grounded strictly in frozen canonical V3.2 research calibration and trading calendar math. Not guaranteed price targets.")

    if entity_type == "STOCK":
        stk_proj = forecast_svc.get_stock_model_projection(
            symbol=selected_entity,
            current_price=curr_price or 100.0,
            parent_industry=p_industry,
            current_date_str=curr_date
        )

        if stk_proj.get("status") == "AVAILABLE":
            fc_c1, fc_c2, fc_c3, fc_c4 = st.columns(4)
            h_data = stk_proj["horizons"]
            
            with fc_c1:
                st.markdown(f"""
                <div style="background: #111622; border: 1px solid #1E2638; border-radius: 6px; padding: 10px 12px;">
                    <div style="font-size: 0.70rem; font-weight: 700; color: #64748B;">1D HORIZON ({h_data['1D']['target_date']})</div>
                    <div style="font-size: 1.10rem; font-weight: 800; color: {'#10B981' if h_data['1D']['exp_return'] > 0 else '#EF4444'};">
                        {h_data['1D']['exp_return']:+.2f}%
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">Implied: ₹{h_data['1D']['proj_price']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with fc_c2:
                st.markdown(f"""
                <div style="background: #111622; border: 1px solid #1E2638; border-radius: 6px; padding: 10px 12px;">
                    <div style="font-size: 0.70rem; font-weight: 700; color: #64748B;">5D HORIZON ({h_data['5D']['target_date']})</div>
                    <div style="font-size: 1.10rem; font-weight: 800; color: {'#10B981' if h_data['5D']['exp_return'] > 0 else '#EF4444'};">
                        {h_data['5D']['exp_return']:+.2f}%
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">Implied: ₹{h_data['5D']['proj_price']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with fc_c3:
                st.markdown(f"""
                <div style="background: #111622; border: 1px solid #00D084; border-radius: 6px; padding: 10px 12px;">
                    <div style="font-size: 0.70rem; font-weight: 700; color: #00D084;">20D CORE HORIZON ({h_data['20D']['target_date']})</div>
                    <div style="font-size: 1.10rem; font-weight: 800; color: {'#10B981' if h_data['20D']['exp_return'] > 0 else '#EF4444'};">
                        {h_data['20D']['exp_return']:+.2f}%
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">Midpoint: ₹{h_data['20D']['proj_price']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            with fc_c4:
                st.markdown(f"""
                <div style="background: #111622; border: 1px solid #1E2638; border-radius: 6px; padding: 10px 12px;">
                    <div style="font-size: 0.70rem; font-weight: 700; color: #64748B;">60D CYCLE ({h_data['60D']['target_date']})</div>
                    <div style="font-size: 1.10rem; font-weight: 800; color: {'#10B981' if h_data['60D']['exp_return'] > 0 else '#EF4444'};">
                        {h_data['60D']['exp_return']:+.2f}%
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">Implied: ₹{h_data['60D']['proj_price']:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

            # 20D Quantile Range Visual Table
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            q_data = stk_proj["quantiles_20d"]
            df_q = pd.DataFrame([
                {"Scenario": q_data["p10"]["label"], "Expected Return": f"{q_data['p10']['ret']:+.2f}%", "Model-Implied Target": f"₹{q_data['p10']['price']:,.2f}", "Probability Weight": "10th Percentile"},
                {"Scenario": q_data["p25"]["label"], "Expected Return": f"{q_data['p25']['ret']:+.2f}%", "Model-Implied Target": f"₹{q_data['p25']['price']:,.2f}", "Probability Weight": "25th Percentile"},
                {"Scenario": q_data["p50"]["label"], "Expected Return": f"{q_data['p50']['ret']:+.2f}%", "Model-Implied Target": f"₹{q_data['p50']['price']:,.2f}", "Probability Weight": "50th Percentile (Median)"},
                {"Scenario": q_data["p75"]["label"], "Expected Return": f"{q_data['p75']['ret']:+.2f}%", "Model-Implied Target": f"₹{q_data['p75']['price']:,.2f}", "Probability Weight": "75th Percentile"},
                {"Scenario": q_data["p90"]["label"], "Expected Return": f"{q_data['p90']['ret']:+.2f}%", "Model-Implied Target": f"₹{q_data['p90']['price']:,.2f}", "Probability Weight": "90th Percentile"}
            ])
            st.dataframe(df_q, use_container_width=True, hide_index=True)
        else:
            st.info(f"ℹ️ {stk_proj.get('message', 'Canonical forecast unavailable for this stock.')}")
    elif entity_type == "INDUSTRY":
        ind_fc = forecast_svc.get_industry_forecast(selected_entity)
        if ind_fc.get("status") == "AVAILABLE":
            t_date_20d = forecast_svc.resolve_future_trading_date(curr_date, 20)
            ic1, ic2, ic3, ic4 = st.columns(4)
            with ic1:
                st.metric("1D Expected Return", f"{ind_fc['exp_return_1d']:+.2f}%")
            with ic2:
                st.metric("5D Expected Return", f"{ind_fc['exp_return_5d']:+.2f}%")
            with ic3:
                st.metric("20D Expected Return", f"{ind_fc['exp_return_20d']:+.2f}%", help=f"Target Date: {t_date_20d}")
            with ic4:
                st.metric("60D Expected Return", f"{ind_fc['exp_return_60d']:+.2f}%")
            
            st.markdown(f"**20D Quantile Range**: P10: `{ind_fc['p10_20d']:+.1f}%` | P25: `{ind_fc['p25_20d']:+.1f}%` | P50: `{ind_fc['p50_20d']:+.1f}%` | P75: `{ind_fc['p75_20d']:+.1f}%` | P90: `{ind_fc['p90_20d']:+.1f}%` | Win Probability: `{ind_fc['prob_win']:.1f}%`")
        else:
            st.info(f"ℹ️ {ind_fc.get('message', 'Forecast unavailable for this industry.')}")
    else:
        st.info("ℹ️ Canonical probabilistic forecasts are modeled at the Basic Industry level. Macro Sector outlook reflects constituent weighted aggregates.")

    # 5. KEY RATING TRANSITIONS MILESTONES TABLE
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-size: 1.05rem; font-weight: 700; color: #F8FAFC;'>🔄 Key Rating Transitions</h4>", unsafe_allow_html=True)
    st.caption("Discrete milestones when the model upgraded or downgraded its conviction.")

    df_trans = query_svc.get_rating_transitions(entity_type, selected_entity, period=period_choice)

    if not df_trans.empty:
        display_rows = []
        for _, row in df_trans.iterrows():
            prev_r = str(row["prev_rating"])
            curr_r = str(row["rating_action"])
            score_delta = row["score"] - row["prev_score"] if pd.notnull(row.get("prev_score")) else 0.0
            sign_str = f"+{score_delta:.1f}" if score_delta > 0 else f"{score_delta:.1f}"
            sc_val = f"{row['score']:.1f} ({sign_str})" if row['score'] > 0 else "Legacy (N/A)"
            
            display_rows.append({
                "Date": row["trade_date"],
                "Previous View": prev_r,
                "New View": curr_r,
                "Conviction Score": sc_val,
                "Flow State": row.get("flow_state") if entity_type != "STOCK" else "—",
                "Reference Price": f"₹{row['close_price']:,.2f}" if pd.notnull(row.get("close_price")) else "—"
            })
        st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Conviction rating remained steady with no transitions during this period.")

    # 6. IMMUTABLE RECORD AUDIT & CRYPTOGRAPHIC PROOF (Progressive Disclosure)
    with st.expander("🛡️ Cryptographic Integrity & Immutable Audit Proof"):
        st.markdown(f"""
        <div style="font-size: 0.80rem; color: #94A3B8; line-height: 1.5;">
            <b>Storage Ledger</b>: <code>data/decision_ledger.db</code> (96.80 MB / Dimensional Schema)<br>
            <b>Model Version Tag</b>: <code>{latest_rec.get('model_version', 'MODEL_V3.2_FROZEN')}</code><br>
            <b>Latest Record Checksum</b>: <code>{latest_rec.get('row_hash', '—')}</code><br>
            <b>Immutability Rule</b>: WORM (Write-Once-Read-Many). Historical snapshots are never altered, retrained, or backfitted.
        </div>
        """, unsafe_allow_html=True)
