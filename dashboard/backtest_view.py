"""
Backtest & Research Dashboard Page.
Visualizes forward returns, hit rates, and alpha generation across money flow strategies.
"""

import streamlit as st
import pandas as pd
from database.db import Database
from analytics.backtesting import StrategyBacktester


def render_backtest_view(db: Database):
    st.subheader("📊 Quantitative Research & Signal Backtesting")
    st.caption("Empirical testing of forward performance following Money Flow and Rotation signals.")

    backtester = StrategyBacktester(db=db)

    col1, col2 = st.columns([3, 2])
    with col1:
        strategy = st.selectbox("Select Signal / Strategy", [
            "SCORE_ABOVE_70",
            "EMERGING_STATE",
            "BREADTH_EXPANSION",
            "VOLUME_EXPANSION"
        ], format_func=lambda x: {
            "SCORE_ABOVE_70": "1. Money Flow Score >= 70 (Strong Flow)",
            "EMERGING_STATE": "2. Rotation State == EMERGING (Early Accel)",
            "BREADTH_EXPANSION": "3. Breadth Surge (>80% >EMA20, >70% Positive)",
            "VOLUME_EXPANSION": "4. Volume Expansion (Vol >= 1.5x, 5D Accel >= +10)"
        }.get(x, x))
    with col2:
        min_stocks = st.slider("Min Constituents for Signal", 1, 10, 2)

    res = backtester.run_signal_backtest(strategy_type=strategy, min_stocks=min_stocks)

    if res.get("total_signals", 0) == 0:
        st.info(f"Summary: {res.get('summary', 'No signals found.')}")
        return

    # KPI ribbon
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Triggered Signals", res["total_signals"])
    with c2:
        st.metric("Avg 5D Forward Return", f"{res['avg_fwd_5d_return']:+.2f}%")
    with c3:
        st.metric("Win Rate (5D > 0)", f"{res['win_rate_5d']:.1f}%")
    with c4:
        st.metric("Alpha vs Benchmark Baseline", f"{res['alpha_vs_baseline']:+.2f}%")

    st.markdown("#### Sample Triggered Signals & Forward Outcomes")
    if res.get("sample_trades"):
        df_samples = pd.DataFrame(res["sample_trades"])
        st.dataframe(df_samples, use_container_width=True, hide_index=True)
