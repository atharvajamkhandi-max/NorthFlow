"""
End-to-End Forensic UI & Reachability Test for Early Sector Radar.
Verifies server HTTP response, sidebar routing, and data generation.
Phase 65B: Early Sector Radar is streamlined into dedicated sidebar navigation.
"""

import urllib.request
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def test_streamlit_server_is_live_and_responding():
    """Verify Streamlit server on port 8501 is running and returns HTTP 200."""
    url = "http://localhost:8501"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as response:
        assert response.status == 200
        html = response.read().decode('utf-8')
        assert "Streamlit" in html or "FLOW" in html or len(html) > 500

def test_app_py_contains_top_level_radar_navigation():
    """Verify app.py has Early Sector Radar in sidebar radio options."""
    app_file = BASE_DIR / "app.py"
    content = app_file.read_text(encoding="utf-8")
    assert "📡 Early Sector Radar (Shadow)" in content
    assert "render_early_sector_radar_ui" in content

def test_phase13_terminal_contains_simplified_core_tabs():
    """Verify phase13_intelligence_terminal.py has the streamlined 4 core tabs."""
    p13_file = BASE_DIR / "dashboard" / "phase13_intelligence_terminal.py"
    content = p13_file.read_text(encoding="utf-8")
    assert "🏛️ Dashboard (Command Center)" in content
    assert "📊 7-Dimension Forensic Profile" in content
    assert "⚖️ Sector Comparison Radar" in content
    assert "📚 Methodology & Model Validation" in content
    # Verify removed redundant duplicate tabs
    assert "🏢 Multi-Segment Conglomerates" not in content

def test_emerging_page_contains_radar_block():
    """Verify emerging.py has the Early Sector Radar precursor block."""
    emg_file = BASE_DIR / "dashboard" / "emerging.py"
    content = emg_file.read_text(encoding="utf-8")
    assert "render_early_sector_radar_ui" in content

def test_radar_service_produces_non_empty_top10_for_latest_date():
    """Verify Early Radar service produces valid non-empty Top 10 for 2026-08-21."""
    from dashboard.components.early_radar_shadow_service import (
        load_point_in_time_industry_history,
        compute_early_radar_scores_point_in_time
    )
    df_hist = load_point_in_time_industry_history("2026-08-21")
    assert not df_hist.empty
    df_scored = compute_early_radar_scores_point_in_time(df_hist)
    df_today = df_scored[df_scored['date'] == pd.to_datetime("2026-08-21")]
    assert len(df_today) >= 10
    assert "early_radar_score" in df_today.columns
    assert "alert_level" in df_today.columns
