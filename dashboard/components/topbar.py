"""
Top Bar Component for Terminal Header.
Phase 71.3: Sanitized institutional command bar with segmented Dark/Light theme switcher.
"""

import streamlit as st
import textwrap
from datetime import datetime
from dashboard.components.global_state import get_hierarchy_metadata, render_hierarchy_badge_inline
from dashboard.components.universe_service import get_current_universe_context
from dashboard.components.theme import get_theme_mode, set_theme_mode, get_theme_tokens

def render_topbar(latest_date: str, page_title: str = "Market Overview"):
    """
    Renders an institutional top command bar with real-time metadata and segmented theme toggle.
    """
    t = get_theme_tokens()
    current_mode = get_theme_mode()
    badge_html = render_hierarchy_badge_inline()

    formatted_date = latest_date
    try:
        dt = datetime.strptime(latest_date, "%Y-%m-%d")
        formatted_date = dt.strftime("%d %b %Y")
    except Exception:
        pass

    col_left, col_right = st.columns([3, 1])
    with col_left:
        html_top = f"""<div style="display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; padding: 2px 0;">
<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
<span style="font-weight: 800; font-size: 1.05rem; color: {t['text_primary']}; letter-spacing: -0.01em;">{page_title}</span>
{badge_html}
</div>
<div style="display: flex; align-items: center; gap: 8px; font-size: 0.74rem; font-family: 'JetBrains Mono', monospace; flex-wrap: wrap;">
<div style="color: {t['text_muted']};">SESSION: <span style="font-weight: 700; color: {t['text_primary']};">{formatted_date}</span></div>
<div style="background-color: {t['positive_bg']}; color: {t['positive']}; border: 1px solid {t['positive_border']}; padding: 1px 6px; border-radius: 4px; font-weight: 700; font-size: 0.62rem;">● CURRENT</div>
</div>
</div>"""
        st.markdown(textwrap.dedent(html_top).strip(), unsafe_allow_html=True)
        
    with col_right:
        btn_lbl = "☀ Light" if current_mode == "light" else "☾ Dark"
        btn_help = f"Currently in {current_mode.upper()} mode. Click to switch."
        if st.button(f"🎨 {btn_lbl}", key=f"btn_theme_toggle_{page_title.lower().replace(' ', '_')}", help=btn_help, use_container_width=True):
            new_mode = "dark" if current_mode == "light" else "light"
            set_theme_mode(new_mode)
            st.rerun()

    border_col = t['card_border']
    st.markdown(f"<div style='border-bottom: 1px solid {border_col}; margin-bottom: 12px;'></div>", unsafe_allow_html=True)
