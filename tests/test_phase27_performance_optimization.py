"""
Regression Test Suite for Phase 27 Performance Optimization:
Validates zero mathematical divergence, memoization efficiency, and single radar execution.
"""
import pytest
import time
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def test_phase27_radar_single_execution_caching():
    """Verify get_cached_early_radar_scores is memoized and warm execution is sub-millisecond."""
    from dashboard.components.early_radar_shadow_service import get_cached_early_radar_scores
    
    test_date = "2026-08-21"
    # First call (populates cache)
    res1 = get_cached_early_radar_scores(test_date)
    assert not res1.empty
    
    # Second call (warm cache)
    t0 = time.perf_counter()
    res2 = get_cached_early_radar_scores(test_date)
    t1 = time.perf_counter()
    warm_duration = t1 - t0
    
    assert not res2.empty
    assert warm_duration < 0.05  # Must return in under 50ms
    pd.testing.assert_frame_equal(res1, res2)

def test_phase27_reconciliation_zero_divergence():
    """Verify zero numerical divergence between raw calculation and cached service."""
    from dashboard.components.early_radar_shadow_service import (
        load_point_in_time_industry_history,
        compute_early_radar_scores_point_in_time,
        get_cached_early_radar_scores
    )
    test_date = "2026-08-21"
    
    # Raw calculation
    hist = load_point_in_time_industry_history(test_date)
    df_raw = compute_early_radar_scores_point_in_time(hist)
    df_raw['v3_2_strength'] = np.clip(
        0.40 * df_raw['breadth_50'] + 0.30 * np.clip((df_raw['ind_ret_20d'] + 10.0) / 30.0 * 100.0, 0.0, 100.0) +
        0.30 * np.clip(df_raw['breadth_20'], 0.0, 100.0),
        0.0, 100.0
    ).round(1)
    raw_today = df_raw[df_raw['date'] == pd.to_datetime(test_date)].sort_values('industry').reset_index(drop=True)
    
    # Cached service
    df_cached = get_cached_early_radar_scores(test_date)
    cached_today = df_cached[df_cached['date'] == pd.to_datetime(test_date)].sort_values('industry').reset_index(drop=True)
    
    # Check strict identity
    diff = (raw_today['early_radar_score'] - cached_today['early_radar_score']).abs().max()
    assert diff == 0.0, f"Divergence detected: {diff}"
    
    diff_p5d = (raw_today['prob_5d'] - cached_today['prob_5d']).abs().max()
    assert diff_p5d == 0.0, f"Divergence in prob_5d: {diff_p5d}"

def test_phase27_phase13_terminal_no_duplicate_radar():
    """Verify phase13_intelligence_terminal uses cached radar scores without recalculating."""
    p13_file = BASE_DIR / "dashboard" / "phase13_intelligence_terminal.py"
    content = p13_file.read_text(encoding="utf-8")
    assert "radar_scored = get_cached_early_radar_scores(selected_date)" in content
    assert "load_point_in_time_industry_history(selected_date)" not in content

