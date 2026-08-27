"""
research/v65c_sidebar/tests/test_sidebar_refinement.py
Isolated unit tests for Phase 65C NorthFlow Sidebar / Left Panel Minimal UI Refinement.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LIVE_DIR = BASE_DIR / "research" / "live_forward"

def test_1_sidebar_all_components_retained_in_app():
    app_file = BASE_DIR / "app.py"
    content = app_file.read_text(encoding="utf-8")
    assert "render_northflow_sidebar_header" in content
    assert "render_global_hierarchy_selector" in content
    assert "render_trading_session_calendar" in content
    assert "MODEL_V3.2_FROZEN" in content
    assert "3,363 Equities & SMEs" in content
    assert "📡 Early Sector Radar (Shadow)" in content
    assert "🔮 Live Forward Validation (Shadow)" in content

def test_2_pitch_black_sidebar_theme():
    theme_file = BASE_DIR / "dashboard" / "components" / "theme.py"
    content = theme_file.read_text(encoding="utf-8")
    assert 'section[data-testid="stSidebar"] {' in content
    assert "background-color: #000000 !important;" in content

def test_3_hierarchy_and_trading_calendar_intact():
    from dashboard.components.global_state import OPTIONS_LIST, HIERARCHY_LEVELS
    assert len(OPTIONS_LIST) == 3
    assert "major_industry" in HIERARCHY_LEVELS
    assert "macro_sector" in HIERARCHY_LEVELS
    assert "specialized_subsector" in HIERARCHY_LEVELS

def test_4_production_immutability_checksums_match():
    pre_file = BASE_DIR / "research" / "v65c_sidebar" / "safety" / "checksums_preflight.json"
    post_file = BASE_DIR / "research" / "v65c_sidebar" / "safety" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
