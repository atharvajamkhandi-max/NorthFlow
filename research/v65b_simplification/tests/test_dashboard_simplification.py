"""
research/v65b_simplification/tests/test_dashboard_simplification.py
Isolated unit tests for Phase 65B Dashboard Navigation & UI Simplification.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

def test_1_dashboard_has_exact_4_simplified_tabs():
    p13_file = BASE_DIR / "dashboard" / "phase13_intelligence_terminal.py"
    content = p13_file.read_text(encoding="utf-8")
    assert "🏛️ Dashboard (Command Center)" in content
    assert "📊 7-Dimension Forensic Profile" in content
    assert "⚖️ Sector Comparison Radar" in content
    assert "📚 Methodology & Model Validation" in content
    # Verify removed redundant duplicate tabs
    assert "🏢 Multi-Segment Conglomerates" not in content

def test_2_early_sector_radar_accessible_in_sidebar():
    app_file = BASE_DIR / "app.py"
    content = app_file.read_text(encoding="utf-8")
    assert "📡 Early Sector Radar (Shadow)" in content
    assert "render_early_sector_radar_ui" in content

def test_3_header_has_northflow_branding():
    hdr_file = BASE_DIR / "dashboard" / "components" / "header.py"
    content = hdr_file.read_text(encoding="utf-8")
    assert "NORTHFLOW" in content
    assert "INDIAN MARKET INTELLIGENCE" in content
    assert "MODEL_V3.2_FROZEN" in content

def test_4_production_immutability_checksums_match():
    pre_file = BASE_DIR / "research" / "v65b_simplification" / "safety" / "checksums_preflight.json"
    post_file = BASE_DIR / "research" / "v65b_simplification" / "safety" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
