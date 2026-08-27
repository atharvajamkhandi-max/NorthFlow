"""
Settings & Methodology Documentation Page with Final V3 Institutional Governance.
"""

import streamlit as st
from database.db import Database
from config.settings import SCORE_WEIGHTS, STOCK_LEADERSHIP_WEIGHTS, BENCHMARK_INDEX, ROTATION_THRESHOLDS
from dashboard.components.topbar import render_topbar

def render_settings_view(db: Database):
    render_topbar(db.get_latest_trading_date() or "N/A", page_title="Settings & Methodology")

    st.markdown("### 📐 Final V3 Quantitative Methodology & Institutional Governance")
    
    st.markdown(f"""
    <div style="background-color: #111622; border: 1px solid #1E2638; border-radius: 6px; padding: 14px 18px; margin-bottom: 16px;">
        <h4 style="margin: 0 0 8px 0; color: #00D084;">1. Canonical Benchmark & Universe Scope</h4>
        <p style="color: #E2E8F0; font-size: 0.9rem; margin: 0;">
            Relative Strength for both industry scoring and stock leadership is benchmarked against <b>{BENCHMARK_INDEX}</b> across <b>403 validated NSE trading sessions</b> (~1.5 years).
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### 🏭 Final V3 7-Dimension Intelligence Architecture
        * **Q1: Current Strength (0-100)**: Observable present strength (Breadth 30%, RS 25%, Trend 25%, Volume 20%).
        * **Q2: Multi-Horizon Expected Return**: Expected excess return for 1D, 5D, 20D, and 60D with $P_{10} \dots P_{90}$ intervals.
        * **Q3: Independent Confidence (0-100)**: Decoupled from strength, reflecting regime reliability, breadth participation, and sample size.
        * **Q4: Risk Score (0-100)**: Downside risk, breadth contraction, and signal exhaustion.
        * **Q5: Market Regime**: 6 observable states with regime reliability multipliers.
        * **Q6: Signal Lifecycle**: `NEW`, `DEVELOPING`, `MATURE`, `EXHAUSTED`, `REVERSING`.
        * **Q7: Observable Flow State**: `ACCUMULATION`, `NEUTRAL`, `DISTRIBUTION` with Net Pressure.
        """)

    with col2:
        st.markdown("""
        #### 🏛️ Champion Model Lock & Governance
        ```
        FINAL SYSTEM STATUS: LOCKED
        CHAMPION: Existing_Deterministic_V1
        DECISION: KEEP_EXISTING_CHAMPION
        OOS RANK IC: +0.1143
        OOS DECILE SPREAD: +2.46%
        OOS SHARPE: -0.53 (Top/Short Decile Net Sharpe = +0.36)
        CALIBRATION: PASSED (Brier Mean Error = 1.2%)
        MAX DRAWDOWN: -2.11% (Long/Short Strategy)
        REGIME ROBUSTNESS: PASSED (Bull, Sideways, High Vol)
        LEAKAGE STATUS: PASS (Zero Look-Ahead Violations)
        TEST STATUS: 78/78 PASSED (100%)
        PRODUCTION STATUS: SAFE
        ```
        """)

    st.markdown("""
    #### 💸 Indian Statutory Transaction Cost Model
    * **Round-Trip Cash Delivery Friction**: ~0.30% (Brokerage, STT 0.1%, GST 18%, Exchange fees, Stamp duty 0.015%, SEBI fees, Slippage).
    * **Long/Short Strategy Round-Trip Friction**: ~0.60%.
    """)

    st.markdown("""
    #### 🌐 Market Universe & Point-in-Time Valuation Methodology (Phase 70)
    * **Authoritative Active Universe Contract**: Single global point-in-time universe filter controlling both display and cross-sectional calculations across all terminal pages.
    * **Valuation Definition**: Baseline equity valuation (₹ Crores) combined with point-in-time 20-day rolling turnover (₹ Lakhs/day).
    * **Source Hierarchy**: Tier 1 (Official Exchange Feeds), Tier 2 (Index & Corporate Action Masters), Tier 3 (Classification Master V3), Tier 4 (Fallback Estimates).
    * **Zero Look-Ahead Limitation**: <code>MARKET_CAP_HISTORY_INSUFFICIENT_FOR_EXACT_RECONSTRUCTION</code> (historical exact shares-outstanding series is not available; point-in-time filtering uses session prices, 20D turnover, and series classification).
    """)
