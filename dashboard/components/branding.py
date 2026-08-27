"""
dashboard/components/branding.py
NorthFlow Institutional Terminal Branding & Trust System.
Phase 71.3: Dynamic theme-aware brand header and footer.
"""

import streamlit as st
import textwrap
from dashboard.components.theme import get_theme_tokens

NORTHFLOW_BRAND = {
    "name": "NORTHFLOW",
    "descriptor": "INDIAN MARKET INTELLIGENCE",
    "version": "v3.2-Production",
    "shadow_version": "v3.4-Shadow-Candidate",
    "subtitle": "Indian Market Intelligence",
    "icon": "🧭",
    "model_version": "MODEL_V3.2_FROZEN",
    "coverage": "3,363 Equities & SMEs",
    "reproducibility": "100% Deterministic Reproducibility",
    "disclaimer": "Quantitative Research & Execution Architecture",
    "theme_colors": {
        "bg_root": "#000000",
        "text_main": "#F8FAFC",
        "accent_blue": "#38BDF8",
        "accent_emerald": "#10B981"
    }
}

def render_northflow_sidebar_header():
    """Renders the institutional brand header at the top of the sidebar."""
    t = get_theme_tokens()
    raw_html = f"""<div style="padding: 2px 0 10px 0; border-bottom: 1px solid {t['sidebar_border']}; margin-bottom: 8px;">
<div style="display: flex; align-items: center; gap: 8px;">
<div style="width: 26px; height: 26px; border-radius: 5px; background: {t['accent_muted']}; border: 1px solid {t['accent']}; display: flex; align-items: center; justify-content: center; font-size: 0.85rem;">
🧭
</div>
<div>
<div style="font-size: 0.95rem; font-weight: 800; color: {t['text_primary']}; letter-spacing: -0.02em; line-height: 1.1;">NORTHFLOW</div>
<div style="font-size: 0.62rem; color: {t['text_muted']}; font-weight: 600; letter-spacing: 0.04em;">Indian Market Intelligence</div>
</div>
</div>
</div>"""
    st.sidebar.markdown(textwrap.dedent(raw_html).strip(), unsafe_allow_html=True)

def render_northflow_trust_footer():
    """Renders the institutional trust & provenance footer at the bottom of the page."""
    t = get_theme_tokens()
    raw_html = f"""<div style="margin-top: 40px; padding: 12px 14px; border-top: 1px solid {t['card_border']}; display: flex; justify-content: space-between; align-items: center; font-size: 0.70rem; color: {t['text_dim']}; font-family: 'JetBrains Mono', monospace;">
<div>
<span style="font-weight: 700; color: {t['text_muted']};">NORTHFLOW TERMINAL</span> · Model Architecture: <b>MODEL_V3.2_FROZEN</b>
</div>
<div>
Coverage: <b>3,363 Equities & SMEs</b> · 100% Deterministic Reproducibility
</div>
</div>"""
    st.markdown(textwrap.dedent(raw_html).strip(), unsafe_allow_html=True)
