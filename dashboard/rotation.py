"""
Rotation Map Page: 4-Quadrant Visual Market Rotation Scatter Plot.
Integrated with the Universal Global Hierarchy & Aggregation Lens.
"""

import streamlit as st
import pandas as pd
from database.db import Database
from dashboard.components.topbar import render_topbar
from dashboard.components.charts import plot_industry_landscape_matrix
from dashboard.components.global_state import get_hierarchy_metadata, render_hierarchy_badge_inline
from dashboard.components.hierarchy_service import get_aggregated_hierarchy_intelligence

def render_rotation_map(db: Database, selected_date: str):
    meta = get_hierarchy_metadata()
    level_label = meta["label"]
    level_plural = meta["plural"]
    badge_html = render_hierarchy_badge_inline()

    render_topbar(selected_date, page_title=f"{level_label} Rotation Map")

    # Authoritative Active Universe Contract
    from dashboard.components.universe_service import get_current_universe_context, render_universe_status_chip
    u_ctx = get_current_universe_context(selected_date)
    render_universe_status_chip(u_ctx)

    eligible_syms_tuple = u_ctx["eligible_symbols_tuple"] if u_ctx["is_filtered"] else None
    df_data, market_meta = get_aggregated_hierarchy_intelligence(selected_date, hierarchy_level_key=None, eligible_symbols=eligible_syms_tuple)
    if df_data.empty:
        st.warning(f"No metric data available for active market universe on {selected_date}.")
        return

    # Filter by minimum stocks
    min_stocks = st.slider("Filter Minimum Constituent Stocks", min_value=1, max_value=15, value=2, step=1, key="rot_min_stocks")
    filtered_df = df_data[df_data['constituent_count'] >= min_stocks].copy()

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 0.88rem; font-weight: 700; color: #94A3B8;">ROTATION MATRIX ({len(filtered_df)} {level_plural.upper()})</span>
        <div>{badge_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # Render Plotly Scatter Map with active hierarchy labels
    fig = plot_industry_landscape_matrix(filtered_df, horizon="20D", label_col="entity_name")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; font-size: 0.8rem;">
        <div style="background-color: #111622; border: 1px solid #1E2638; padding: 10px; border-radius: 6px;">
            <b style="color: #10B981;">↗ LEADING / LEADERS</b><br>
            <span style="color: #64748B;">High Strength + Strong Relative Strength. Prime focus for trend leaders.</span>
        </div>
        <div style="background-color: #111622; border: 1px solid #1E2638; padding: 10px; border-radius: 6px;">
            <b style="color: #0EA5E9;">↖ IMPROVING / EARLY</b><br>
            <span style="color: #64748B;">Money flowing in + recovering price. Early accumulation setups.</span>
        </div>
        <div style="background-color: #111622; border: 1px solid #1E2638; padding: 10px; border-radius: 6px;">
            <b style="color: #F59E0B;">↘ WEAKENING / COOLING</b><br>
            <span style="color: #64748B;">High price but decelerating money flow. Profit booking phase.</span>
        </div>
        <div style="background-color: #111622; border: 1px solid #1E2638; padding: 10px; border-radius: 6px;">
            <b style="color: #EF4444;">↙ LAGGING / WEAK</b><br>
            <span style="color: #64748B;">Low strength + negative momentum. Underperforming asset basket.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
