"""
dashboard/components/navigation.py
NorthFlow Institutional Grouped Sidebar Navigation Rail.
Phase 71.3: Clean grouped sections (COMMAND, MARKET, DISCOVERY, RESEARCH, SYSTEM)
with full human-readable labels, active indicator, and zero bullet artifacts.
"""

import streamlit as st
from typing import Dict, List, Tuple, Any
from dashboard.components.theme import get_theme_tokens

NAV_GROUPS: List[Dict[str, Any]] = [
    {
        "category": "COMMAND",
        "items": [
            ("📈 Market Overview", "Executive Macro Regime & Market Overview Intelligence"),
            ("🎯 Quality Picks & Trade Tracker", "Daily, Weekly, Monthly, Long-Term Setups with Stop-Loss & Target Lifecycle Ledger"),
            ("🎯 Industry Intelligence", "Industry Intelligence Cockpit & Top Roster")
        ]
    },
    {
        "category": "MARKET",
        "items": [
            ("🌊 Industry Flow", "Cross-Sectional Screener & Constituent Drilldown"),
            ("🔄 Rotation Map", "Leading, Improving, Weakening & Lagging Quadrants")
        ]
    },
    {
        "category": "DISCOVERY",
        "items": [
            ("📡 Early Sector Radar (Shadow)", "Leading Indicator Momentum Signals"),
            ("🚀 Emerging Rotations", "Early Capital Inflow & Acceleration Spikes"),
            ("🏭 Industries Explorer", "Hierarchy Directory & Deep-Dive Analytics"),
            ("⚡ Stock Screener", "Multi-Factor Metric Filtering & Equity Search")
        ]
    },
    {
        "category": "RESEARCH",
        "items": [
            ("🔮 Live Forward Validation (Shadow)", "Out-of-Sample Performance Audit & Ledger"),
            ("🧠 Historical Decision Memory", "Point-in-Time Audit & Model Memory")
        ]
    },
    {
        "category": "SYSTEM",
        "items": [
            ("🛡️ Data Health", "Pipeline Freshness & Data Quality Audits"),
            ("⚙️ Settings & Methodology", "Model Architecture & System Specifications")
        ]
    }
]

def render_grouped_navigation() -> str:
    """
    Renders institutional grouped navigation in the sidebar.
    Returns the currently active page name.
    """
    t = get_theme_tokens()
    
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "📈 Market Overview"
        
    curr_active = st.session_state["nav_page"]

    # Flat list of all valid page names
    all_pages = [item[0] for g in NAV_GROUPS for item in g["items"]]
    if curr_active not in all_pages:
        curr_active = all_pages[0]
        st.session_state["nav_page"] = curr_active

    for g_idx, group in enumerate(NAV_GROUPS):
        cat_title = group["category"]
        st.sidebar.markdown(f"""
        <div style="font-size: 0.60rem; font-weight: 800; color: {t['text_dim']}; text-transform: uppercase; letter-spacing: 0.12em; margin-top: 10px; margin-bottom: 2px; padding-left: 2px;">
            {cat_title}
        </div>
        """, unsafe_allow_html=True)
        
        for item_name, item_desc in group["items"]:
            is_active = (item_name == curr_active)
            btn_key = f"nav_btn_{g_idx}_{item_name.split()[0]}_{hash(item_name)}"
            
            # Use Streamlit native button styled with CSS
            btn_type = "primary" if is_active else "secondary"
            if st.sidebar.button(item_name, key=btn_key, type=btn_type, use_container_width=True):
                if curr_active != item_name:
                    st.session_state["nav_page"] = item_name
                    st.rerun()

    return st.session_state["nav_page"]
