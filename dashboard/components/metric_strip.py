"""
Compact Market Intelligence Strip Component.
Shows top-level metrics in a dense terminal layout.
"""

import streamlit as st
import pandas as pd

def render_metric_strip(df_ind: pd.DataFrame, latest_date: str):
    """
    Renders a compact 5-stat intelligence strip using actual database metrics.
    """
    if df_ind.empty:
        return

    total_inds = len(df_ind)
    strong_cnt = len(df_ind[df_ind['status'].isin(['STRONG', 'STRENGTHENING'])])
    emerging_cnt = len(df_ind[df_ind['status'] == 'EMERGING'])
    cooling_cnt = len(df_ind[df_ind['status'].isin(['COOLING', 'WEAKENING', 'EXHAUSTION'])])
    avg_breadth = df_ind['ema20_breadth'].mean() if 'ema20_breadth' in df_ind.columns else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("INDUSTRIES", f"{total_inds}", delta=None)
    with c2:
        st.metric("STRONG / LEADING", f"{strong_cnt}", delta=f"{(strong_cnt/total_inds)*100:.0f}%" if total_inds else None)
    with c3:
        st.metric("EMERGING", f"{emerging_cnt}", delta=f"{(emerging_cnt/total_inds)*100:.0f}%" if total_inds else None)
    with c4:
        st.metric("COOLING / WEAK", f"{cooling_cnt}", delta=f"-{(cooling_cnt/total_inds)*100:.0f}%" if total_inds else None, delta_color="inverse")
    with c5:
        st.metric("AVG > EMA20 BREADTH", f"{avg_breadth:.1f}%", delta=None)
