"""
Global Cockpit Header Bar Component
NORTHFLOW - Indian Market Intelligence Terminal
Phase 67: Clean, Institutional Terminal Cockpit Header with Active Universe & Regime Metadata.
"""

import streamlit as st
import textwrap
from dashboard.components.global_state import get_hierarchy_metadata, render_hierarchy_badge_inline
from dashboard.components.universe_service import get_current_universe_context

def render_cockpit_header(selected_date: str, total_sessions: int = 403, regime_label: str = "BULLISH", regime_score: float = 74.0):
    """Renders the top global cockpit status and macro metrics bar."""
    meta = get_hierarchy_metadata()
    regime_class = "regime-badge-bullish" if "BULL" in regime_label.upper() else ("regime-badge-neutral" if "NEUT" in regime_label.upper() else "regime-badge-bearish")
    badge_html = render_hierarchy_badge_inline()

    u_ctx = get_current_universe_context(selected_date)
    universe_txt = u_ctx["chip_label"]
    stocks_txt = f"{u_ctx['eligible_count']:,} STOCKS"

    html = f"""<div class="cockpit-header-bar" data-model="MODEL_V3.2_FROZEN">
<div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
<div style="display: flex; align-items: center; gap: 8px;">
<div style="width: 24px; height: 24px; border-radius: 4px; background: linear-gradient(135deg, #1D4ED8 0%, #38BDF8 100%); display: flex; align-items: center; justify-content: center; font-weight: 900; color: #FFFFFF; font-size: 12px; letter-spacing: -0.02em;">N</div>
<div>
<div style="font-size: 1.05rem; font-weight: 800; color: #F8FAFC; letter-spacing: 0.04em; line-height: 1.1; font-family: 'Plus Jakarta Sans', sans-serif;">NORTH<span style="color: #38BDF8;">FLOW</span></div>
<div style="font-size: 0.58rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.10em;">INDIAN MARKET INTELLIGENCE</div>
</div>
</div>
<div style="height: 20px; width: 1px; background: #151F38; margin: 0 4px;"></div>
<div style="display: flex; align-items: center; gap: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;">
<span style="color: #64748B; font-weight: 700;">SESSION:</span>
<span style="color: #F8FAFC; font-weight: 700;">{selected_date}</span>
<span style="color: #64748B;">|</span>
<span style="color: #10B981; font-weight: 700;">● DATA CURRENT</span>
<span style="color: #64748B;">|</span>
<span style="color: #38BDF8; font-weight: 700;">UNIVERSE: {universe_txt}</span>
<span style="background: rgba(56, 189, 248, 0.10); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.25); padding: 1px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: 700;">{stocks_txt}</span>
</div>
<div style="margin-left: 4px;">{badge_html}</div>
</div>
<div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
<div style="display: flex; align-items: center; gap: 8px;">
<span style="font-size: 0.68rem; color: #64748B; font-weight: 700;">REGIME:</span>
<span class="{regime_class}">{regime_label} ({regime_score:.0f}/100)</span>
</div>
<div style="height: 18px; width: 1px; background: #151F38;"></div>
<div style="display: flex; align-items: center; gap: 12px; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;">
<div><span style="color: #64748B;">NIFTY 500:</span> <span style="color: #10B981; font-weight: 700;">24,812.40 +0.71%</span></div>
<div><span style="color: #64748B;">INDIA VIX:</span> <span style="color: #38BDF8; font-weight: 700;">13.28 -2.41%</span></div>
<div><span style="color: #64748B;">ADV/DEC:</span> <span style="color: #10B981; font-weight: 700;">336</span> / <span style="color: #EF4444; font-weight: 700;">164</span></div>
</div>
</div>
</div>"""
    st.markdown(textwrap.dedent(html), unsafe_allow_html=True)
