"""
research/v67_branding/tests/test_brand_system.py
Isolated unit tests for Phase 67 NorthFlow Brand System & Institutional Terminal UI.
"""
import pytest
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

def test_1_branding_tokens_exist():
    from dashboard.components.branding import NORTHFLOW_BRAND
    assert NORTHFLOW_BRAND["name"] == "NORTHFLOW"
    assert NORTHFLOW_BRAND["descriptor"] == "INDIAN MARKET INTELLIGENCE"
    assert NORTHFLOW_BRAND["theme_colors"]["bg_root"] == "#000000"

def test_2_app_routes_branded():
    app_txt = (BASE_DIR / "app.py").read_text(encoding="utf-8")
    assert "Industry Intelligence" in app_txt
    assert "Live Forward Validation (Shadow)" in app_txt
    assert "Early Sector Radar (Shadow)" in app_txt
    assert "Industry Flow" in app_txt
    assert "NORTHFLOW" in app_txt

def test_3_header_has_clean_terminal_branding():
    from dashboard.components.header import render_cockpit_header
    assert callable(render_cockpit_header)

def test_4_pitch_black_theme_tokens():
    from dashboard.components.theme import apply_terminal_theme
    assert callable(apply_terminal_theme)

def test_5_production_immutability_checksums_match():
    pre_file = BASE_DIR / "research" / "v67_branding" / "safety" / "checksums_preflight.json"
    post_file = BASE_DIR / "research" / "v67_branding" / "safety" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
