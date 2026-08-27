"""
research/v65b_branding/tests/test_northflow_branding.py
Isolated unit tests for Phase 65B NorthFlow Brand Identity & System Tokens.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LIVE_DIR = BASE_DIR / "research" / "live_forward"

def test_1_branding_module_and_tokens_exist():
    b_file = BASE_DIR / "dashboard" / "components" / "branding.py"
    assert b_file.exists()
    from dashboard.components.branding import NORTHFLOW_BRAND
    assert NORTHFLOW_BRAND["name"] == "NORTHFLOW"
    assert NORTHFLOW_BRAND["descriptor"] == "INDIAN MARKET INTELLIGENCE"

def test_2_app_renders_northflow_header_and_footer():
    app_file = BASE_DIR / "app.py"
    with open(app_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "NORTHFLOW" in content
    assert "render_northflow_sidebar_header" in content
    assert "render_northflow_trust_footer" in content

def test_3_production_model_separation_in_branding():
    from dashboard.components.branding import NORTHFLOW_BRAND
    assert NORTHFLOW_BRAND["version"] == "v3.2-Production"
    assert NORTHFLOW_BRAND["shadow_version"] == "v3.4-Shadow-Candidate"

def test_4_production_immutability_checksums_match():
    pre_file = BASE_DIR / "research" / "v65b_branding" / "safety" / "checksums_preflight.json"
    post_file = BASE_DIR / "research" / "v65b_branding" / "safety" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
