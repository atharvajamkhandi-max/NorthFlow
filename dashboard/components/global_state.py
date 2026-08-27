"""
Global Application State, Hierarchy Lens & Market Universe Filter Management.
Single Source of Truth for Hierarchy, Market Universe, Trading Session, and Active Filters.
Phase 71.3: Dynamic theme-aware sidebar lens and universe controls.
"""

import streamlit as st
import textwrap
from typing import Dict, Any, Tuple, Optional
from dashboard.components.theme import get_theme_tokens

# Supported Hierarchy Levels
HIERARCHY_LEVELS = {
    "major_industry": {
        "key": "major_industry",
        "col": "industry",
        "label": "Major Industry",
        "plural": "Major Industries",
        "badge": "[ MAJOR INDUSTRY ]",
        "description": "168 Disaggregated Business Segments (Default)",
        "icon": "🎯",
        "color": "#10B981"
    },
    "macro_sector": {
        "key": "macro_sector",
        "col": "macro_sector",
        "label": "Macro Sector",
        "plural": "Macro Sectors",
        "badge": "[ MACRO SECTOR ]",
        "description": "48 Direct Real-World Operating Domains",
        "icon": "🏛️",
        "color": "#0EA5E9"
    },
    "specialized_subsector": {
        "key": "specialized_subsector",
        "col": "basic_industry",
        "label": "Specialization Subsector",
        "plural": "Specialization Subsectors",
        "badge": "[ SPECIALIZED SUBSECTOR ]",
        "description": "168 Niche Competitive Positions",
        "icon": "🔍",
        "color": "#A855F7"
    }
}

OPTIONS_LIST = [
    "Major Industry (Recommended Default)",
    "Macro Sector (High-Level)",
    "Specialized Subsector (Niche)"
]

KEY_MAP = {
    "Major Industry (Recommended Default)": "major_industry",
    "Macro Sector (High-Level)": "macro_sector",
    "Specialized Subsector (Niche)": "specialized_subsector"
}
REVERSE_MAP = {v: k for k, v in KEY_MAP.items()}

def init_global_state():
    """Initializes global state variables if not already present in session_state."""
    if "hierarchy_level" not in st.session_state:
        st.session_state["hierarchy_level"] = "major_industry"
    if "universe_preset" not in st.session_state:
        st.session_state["universe_preset"] = "all"
    if "universe_custom_include_sme" not in st.session_state:
        st.session_state["universe_custom_include_sme"] = True
    if "universe_custom_min_mcap" not in st.session_state:
        st.session_state["universe_custom_min_mcap"] = 0.0
    if "universe_custom_min_turnover" not in st.session_state:
        st.session_state["universe_custom_min_turnover"] = 0.0

def get_hierarchy_level() -> str:
    """Returns the active hierarchy key ('major_industry', 'macro_sector', 'specialized_subsector')."""
    init_global_state()
    if "global_hierarchy_select" in st.session_state:
        sel_val = st.session_state["global_hierarchy_select"]
        if sel_val in KEY_MAP:
            st.session_state["hierarchy_level"] = KEY_MAP[sel_val]
    
    level = st.session_state.get("hierarchy_level", "major_industry")
    if level not in HIERARCHY_LEVELS:
        level = "major_industry"
        st.session_state["hierarchy_level"] = level
    return level

def get_hierarchy_metadata() -> Dict[str, Any]:
    """Returns metadata dictionary for the currently active hierarchy level."""
    return HIERARCHY_LEVELS[get_hierarchy_level()]

def set_hierarchy_level(level_key: str):
    """Updates the active hierarchy level in global session state."""
    if level_key in HIERARCHY_LEVELS:
        st.session_state["hierarchy_level"] = level_key
        if level_key in REVERSE_MAP:
            st.session_state["global_hierarchy_select"] = REVERSE_MAP[level_key]

def render_global_hierarchy_selector():
    """Renders the compact collapsible Analytical Lens selector in the sidebar."""
    t = get_theme_tokens()
    init_global_state()
    current_key = get_hierarchy_level()
    current_option_label = REVERSE_MAP.get(current_key, OPTIONS_LIST[0])

    st.sidebar.markdown(f"""
    <div style="font-size: 0.60rem; font-weight: 800; color: {t['text_dim']}; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 2px;">
        ANALYTICAL LENS
    </div>
    """, unsafe_allow_html=True)

    curr_idx = OPTIONS_LIST.index(current_option_label) if current_option_label in OPTIONS_LIST else 0
    selected_option = st.sidebar.selectbox(
        "Select Lens",
        options=OPTIONS_LIST,
        index=curr_idx,
        key="global_hierarchy_select",
        label_visibility="collapsed"
    )
    if selected_option in KEY_MAP:
        st.session_state["hierarchy_level"] = KEY_MAP[selected_option]

    meta = get_hierarchy_metadata()
    lens_html = f"""<div style="padding: 2px 0 6px 0; margin-bottom: 6px;">
<div style="display: flex; align-items: center; justify-content: space-between;">
<span style="font-size: 0.60rem; color: {t['text_dim']}; font-weight: 700;">ACTIVE LENS</span>
<span style="font-size: 0.68rem; color: {meta['color']}; font-weight: 700; font-family: 'JetBrains Mono';">{meta['badge']}</span>
</div>
<div style="font-size: 0.65rem; color: {t['text_muted']}; margin-top: 1px;">{meta['description']}</div>
</div>"""
    st.sidebar.markdown(textwrap.dedent(lens_html).strip(), unsafe_allow_html=True)

def render_market_universe_selector(selected_date: str):
    """Renders the dedicated compact Market Universe selector in the sidebar."""
    t = get_theme_tokens()
    from dashboard.components.universe_service import UNIVERSE_PRESETS, get_current_universe_context

    st.sidebar.markdown(f"""
    <div style="font-size: 0.60rem; font-weight: 800; color: {t['text_dim']}; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 2px;">
        MARKET UNIVERSE
    </div>
    """, unsafe_allow_html=True)

    preset_keys = list(UNIVERSE_PRESETS.keys())
    preset_labels = [UNIVERSE_PRESETS[k]["label"] for k in preset_keys]

    curr_preset = st.session_state.get("universe_preset", "all")
    curr_idx = preset_keys.index(curr_preset) if curr_preset in preset_keys else 0

    selected_label = st.sidebar.selectbox(
        "Select Universe Filter",
        options=preset_labels,
        index=curr_idx,
        key="sb_universe_preset_select",
        label_visibility="collapsed"
    )
    new_preset_key = preset_keys[preset_labels.index(selected_label)]
    st.session_state["universe_preset"] = new_preset_key

    # If custom universe is chosen, show compact sub-controls
    if new_preset_key == "custom":
        c_sme = st.sidebar.checkbox("Include SME Platform (SM/ST)", value=st.session_state.get("universe_custom_include_sme", True), key="chk_custom_sme")
        st.session_state["universe_custom_include_sme"] = c_sme

        mcap_val = st.sidebar.number_input("Min Market Cap (₹ Cr)", min_value=0.0, max_value=500000.0, value=float(st.session_state.get("universe_custom_min_mcap", 0.0)), step=100.0, key="num_custom_mcap")
        st.session_state["universe_custom_min_mcap"] = mcap_val

        turn_val = st.sidebar.number_input("Min 20D Turnover (₹ Lakhs/d)", min_value=0.0, max_value=10000.0, value=float(st.session_state.get("universe_custom_min_turnover", 0.0)), step=10.0, key="num_custom_turnover")
        st.session_state["universe_custom_min_turnover"] = turn_val

    # Query context
    u_ctx = get_current_universe_context(selected_date)
    sme_badge_color = t['positive'] if u_ctx["include_sme"] else t['warning']
    sme_txt = "INCLUDED" if u_ctx["include_sme"] else "EXCLUDED"

    u_html = f"""<div style="padding: 2px 0 6px 0; border-bottom: 1px solid {t['sidebar_border']}; margin-bottom: 6px;">
<div style="display: flex; justify-content: space-between; align-items: center;">
<span style="font-size: 0.60rem; color: {t['text_dim']}; font-weight: 700;">ELIGIBLE STOCKS</span>
<span style="font-size: 0.68rem; color: {t['accent']}; font-weight: 700; font-family: 'JetBrains Mono';">{u_ctx['eligible_count']:,} ({u_ctx['coverage_pct']}%)</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1px; font-size: 0.65rem; color: {t['text_muted']};">
<span>SME Platform:</span>
<span style="color: {sme_badge_color}; font-weight: 700;">{sme_txt}</span>
</div>
</div>"""
    st.sidebar.markdown(textwrap.dedent(u_html).strip(), unsafe_allow_html=True)

def render_hierarchy_badge_inline() -> str:
    """Returns HTML snippet for the active hierarchy badge pill."""
    meta = get_hierarchy_metadata()
    return f"""<span style="background: rgba(14, 165, 233, 0.12); color: {meta['color']}; border: 1px solid {meta['color']}44; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 800; font-family: 'JetBrains Mono'; letter-spacing: 0.04em;">{meta['badge']}</span>"""
