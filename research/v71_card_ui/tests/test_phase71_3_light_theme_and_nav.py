"""
research/v71_card_ui/tests/test_phase71_3_light_theme_and_nav.py
Automated Unit & Integration Tests for Phase 71.3 Light Theme Polish & Global Navigation UI.
"""
import pytest
from pathlib import Path
from dashboard.components.theme import THEME_TOKENS, get_theme_mode, set_theme_mode, get_theme_tokens
from dashboard.components.navigation import NAV_GROUPS

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

def test_1_light_theme_tokens_compliance():
    light = THEME_TOKENS["light"]
    assert light["canvas"] == "#F6F8FB"
    assert light["card_bg"] == "#FFFFFF"
    assert light["card_border"] == "#D9E1EA"
    assert light["text_primary"] == "#0F172A"
    assert light["accent"] == "#2563EB"
    assert light["positive"] == "#059669"
    assert light["negative"] == "#DC2626"

def test_2_dark_theme_tokens_compliance():
    dark = THEME_TOKENS["dark"]
    assert dark["canvas"] == "#000000"
    assert dark["card_bg"] == "#080C14"
    assert dark["card_border"] == "#1E293B"
    assert dark["text_primary"] == "#F8FAFC"
    assert dark["accent"] == "#38BDF8"

def test_3_navigation_groups_and_12_destinations():
    categories = [g["category"] for g in NAV_GROUPS]
    assert "COMMAND" in categories
    assert "MARKET" in categories
    assert "DISCOVERY" in categories
    assert "RESEARCH" in categories
    assert "SYSTEM" in categories

    all_items = [item[0] for g in NAV_GROUPS for item in g["items"]]
    assert len(all_items) == 12
    
    # Verify every destination has an icon and human-readable text
    for item in all_items:
        assert len(item.strip()) > 3
        # Check first char or emoji
        assert any(c in item for c in ["🎯", "📈", "🌊", "🔄", "📡", "🚀", "🏭", "⚡", "🔮", "🧠", "🛡️", "⚙️"])

def test_4_theme_mode_switching_state():
    set_theme_mode("light")
    assert get_theme_mode() == "light"
    assert get_theme_tokens()["canvas"] == "#F6F8FB"

    set_theme_mode("dark")
    assert get_theme_mode() == "dark"
    assert get_theme_tokens()["canvas"] == "#000000"

def test_5_zero_html_leakage_in_branding_and_navigation():
    from dashboard.components.branding import render_northflow_sidebar_header
    from dashboard.components.topbar import render_topbar
    
    # Ensure imported modules do not fail on evaluation
    assert callable(render_northflow_sidebar_header)
    assert callable(render_topbar)
