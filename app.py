"""
Main Streamlit Application Entrypoint.
NORTHFLOW — Indian Market Intelligence Terminal.
Professional Quantitative Trading & Research Platform.
Production Architecture: MODEL_V3.2_FROZEN (Active & Frozen).
Coverage Universe: 3,363 Equities & SMEs (Active Market Universe).
Phase 71.3: Institutional Light Theme Polish & Grouped Sidebar Navigation Rail.
"""

import sys
from pathlib import Path
import streamlit as st

# Setup page config
st.set_page_config(
    page_title="NORTHFLOW | Indian Market Intelligence",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.db import Database
from dashboard.components.theme import apply_terminal_theme
from dashboard.components.branding import render_northflow_sidebar_header, render_northflow_trust_footer
from dashboard.components.global_state import (
    init_global_state,
    render_global_hierarchy_selector,
    render_market_universe_selector,
    get_hierarchy_metadata
)
from dashboard.components.universe_service import get_current_universe_context, render_universe_status_chip
from dashboard.components.trading_calendar import render_trading_session_calendar
from dashboard.components.navigation import render_grouped_navigation

from dashboard.overview import render_overview
from dashboard.industry_flow import render_industry_flow
from dashboard.emerging import render_emerging
from dashboard.rotation import render_rotation_map
from dashboard.industries_explorer import render_industries_explorer
from dashboard.industry_detail import render_industry_detail
from dashboard.phase13_intelligence_terminal import render_phase13_intelligence_terminal
from dashboard.stock_screener import render_stock_screener
from dashboard.data_quality import render_data_quality
from dashboard.settings_view import render_settings_view

def main():
    # Initialize global state & inject NorthFlow theme
    init_global_state()
    apply_terminal_theme()

    db = Database()
    dates = db.get_existing_price_dates()

    if not dates:
        st.warning("⚠️ Database is empty. Please run initial setup first:")
        st.code("python scripts/initial_setup.py --days 30", language="bash")
        return

    # NorthFlow Sidebar Header
    render_northflow_sidebar_header()

    # 1. Collapsible Analytical Lens Selector
    render_global_hierarchy_selector()

    # 2. Interactive Calendar Date Selector & Navigation
    selected_date = render_trading_session_calendar(db)

    # 3. Market Universe Selector
    render_market_universe_selector(selected_date)

    # 4. Grouped Institutional Navigation Rail
    page = render_grouped_navigation()

    # Route page
    if page == "🎯 Industry Intelligence":
        render_phase13_intelligence_terminal(db, selected_date)
    elif page == "🔮 Live Forward Validation (Shadow)":
        from dashboard.live_forward_validation_ui import render_live_forward_validation_ui
        render_live_forward_validation_ui(selected_date)
    elif page == "📡 Early Sector Radar (Shadow)":
        from dashboard.components.early_radar_shadow_service import render_early_sector_radar_ui
        render_early_sector_radar_ui(selected_date)
    elif page == "🧠 Historical Decision Memory":
        from dashboard.decision_memory import render_decision_memory_ui
        render_decision_memory_ui(db, selected_date)
    elif page == "📈 Market Overview":
        render_overview(db, selected_date)
    elif page == "🌊 Industry Flow":
        render_industry_flow(db, selected_date)
    elif page == "🚀 Emerging Rotations":
        render_emerging(db, selected_date)
    elif page == "🔄 Rotation Map":
        render_rotation_map(db, selected_date)
    elif page == "🏭 Industries Explorer":
        render_industries_explorer(db, selected_date)
    elif page == "⚡ Stock Screener":
        render_stock_screener(db, selected_date)
    elif page == "🛡️ Data Health":
        render_data_quality(db)
    elif page == "⚙️ Settings & Methodology":
        render_settings_view(db)

    # NorthFlow Trust Footer
    render_northflow_trust_footer()

if __name__ == "__main__":
    main()
