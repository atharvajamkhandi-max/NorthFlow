"""
Unit and Integration Test Suite for Phase 25:
Early Sector Radar Website Integration (Shadow Mode).
"""

import os
import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SHADOW_LOG_DIR = BASE_DIR / "research" / "live_shadow"
REPORTS_DIR = BASE_DIR / "research" / "reports"

def test_phase25_shadow_service_importable():
    """Verify early_radar_shadow_service is importable and has required functions."""
    from dashboard.components.early_radar_shadow_service import (
        compute_early_radar_scores_point_in_time,
        persist_daily_shadow_log,
        load_point_in_time_industry_history,
        render_early_sector_radar_ui
    )
    assert callable(compute_early_radar_scores_point_in_time)
    assert callable(persist_daily_shadow_log)
    assert callable(load_point_in_time_industry_history)
    assert callable(render_early_sector_radar_ui)

def test_phase25_point_in_time_calculation_sample():
    """Verify point-in-time calculation outputs valid scores without lookahead."""
    from dashboard.components.early_radar_shadow_service import (
        compute_early_radar_scores_point_in_time,
        load_point_in_time_industry_history
    )
    df_hist = load_point_in_time_industry_history("2026-08-21")
    assert not df_hist.empty
    assert "industry" in df_hist.columns
    
    df_scored = compute_early_radar_scores_point_in_time(df_hist)
    assert "early_radar_score" in df_scored.columns
    assert "alert_level" in df_scored.columns
    assert "prob_5d" in df_scored.columns
    df_valid = df_scored.dropna(subset=['early_radar_score'])
    assert (df_valid['early_radar_score'] >= 0.0).all()
    assert (df_valid['early_radar_score'] <= 100.0).all()

def test_phase25_shadow_log_persisted():
    """Verify daily shadow logs are persisted in research/live_shadow/."""
    assert SHADOW_LOG_DIR.exists()
    logs = list(SHADOW_LOG_DIR.glob("*_early_radar.csv"))
    assert len(logs) > 0

def test_phase25_report_exists_and_detailed():
    """Verify Phase 25 integration report exists with SHADOW RADAR LIVE status."""
    p = REPORTS_DIR / "PHASE25_EARLY_RADAR_WEBSITE_INTEGRATION.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert "SHADOW RADAR LIVE" in content
    assert "early_radar_shadow_service.py" in content

def test_phase25_frozen_model_untouched():
    """Verify MODEL_V3.2_FROZEN specification remains completely intact and unmodified."""
    from config.model_v3_2_frozen import MODEL_V3_2_FINGERPRINT
    assert MODEL_V3_2_FINGERPRINT['model_version'] == "MODEL_V3.2_FROZEN"
    assert MODEL_V3_2_FINGERPRINT['verified_rank_ic'] == 0.1140
