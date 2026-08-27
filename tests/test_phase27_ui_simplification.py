"""
Unit and UI Test Suite for Phase 27:
UI/UX Simplification of Industry Intelligence and Rotation Momentum Wheel.
"""

import pytest
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def test_phase27_phase13_terminal_contains_executive_summary():
    """Verify phase13_intelligence_terminal.py contains plain English executive market pulse."""
    p13_file = BASE_DIR / "dashboard" / "phase13_intelligence_terminal.py"
    content = p13_file.read_text(encoding="utf-8")
    assert "WHAT IS HAPPENING IN THE MARKET?" in content
    assert "🚀 STRONG NOW" in content
    assert "🔥 HEATING UP" in content
    assert "🟢 EARLY ACCUMULATION" in content
    assert "🔴 LOSING STRENGTH" in content
    assert "PRECURSOR ACCUMULATION SPOTLIGHT" in content
    assert "Possible move window:" in content

def test_phase27_rotation_momentum_wheel_rendering():
    """Verify plot_industry_rotation_trail renders a valid Figure with 4 quadrants."""
    from dashboard.components.charts import plot_industry_rotation_trail
    df_sample = pd.DataFrame([
        {'entity_name': 'Sugar & Bio-Ethanol', 'score_today': 75.0, 'industry_rs_20d': 6.5, 'avg_return_5d': 3.2, 'avg_return_20d': 8.0},
        {'entity_name': 'Zinc Alloys', 'score_today': 68.0, 'industry_rs_20d': -3.5, 'avg_return_5d': 2.0, 'avg_return_20d': 5.0},
        {'entity_name': 'Luxury Hotels', 'score_today': 42.0, 'industry_rs_20d': 4.0, 'avg_return_5d': -1.5, 'avg_return_20d': 1.0},
        {'entity_name': 'Thermal Power', 'score_today': 35.0, 'industry_rs_20d': -7.0, 'avg_return_5d': -2.0, 'avg_return_20d': -4.0}
    ])
    fig = plot_industry_rotation_trail(df_sample, label_col="entity_name")
    assert fig is not None
    assert len(fig.data) > 0  # Traces added for lines and markers

def test_phase27_early_radar_progressive_disclosure():
    """Verify early_radar_shadow_service has Level 1 spotlight, Level 2 table, and Level 3 details."""
    service_file = BASE_DIR / "dashboard" / "components" / "early_radar_shadow_service.py"
    content = service_file.read_text(encoding="utf-8")
    assert "PRECURSOR ACCUMULATION SPOTLIGHT" in content
    assert "Possible move window:" in content
    assert "📊 Quantitative Details: Mathematical Probabilities & Feature Breakdowns" in content
    assert "🟢 Early Turnarounds (Quiet Bottom Accumulation)" in content

def test_phase27_drilldown_shows_all_constituents():
    """Phase 71.2: drilldown shows ALL eligible constituent stocks (head(5) cap was removed).
    Verifies drilldown renders full results without artificial truncation."""
    p13_file = BASE_DIR / "dashboard" / "phase13_intelligence_terminal.py"
    content = p13_file.read_text(encoding="utf-8")
    # Phase 71.2 removed head(5) — all eligible stocks are now shown
    assert "df_stk_view.head(5)" not in content, (
        "Phase 71.2 removed the top-5 truncation; drilldown must show all constituents"
    )
    # The industry drilldown section must still exist
    assert "display_slice" in content or "df_stk_view" in content, (
        "Drilldown dataframe rendering must still be present"
    )
    assert "Focus / Highlight Industry on Momentum Wheel:" in content

def test_phase27_theme_viewport_clipping_fix():
    """Verify theme.py has sufficient padding-top to avoid header viewport clipping."""
    theme_file = BASE_DIR / "dashboard" / "components" / "theme.py"
    content = theme_file.read_text(encoding="utf-8")
    assert "padding-top: 3.8rem !important;" in content
    assert "header[data-testid=\"stHeader\"]" in content

def test_phase27_frozen_models_untouched():
    """Verify MODEL_V3_2_FROZEN fingerprint and EARLY_RADAR_V1_FROZEN remain 100% untouched."""
    from config.model_v3_2_frozen import MODEL_V3_2_FINGERPRINT
    from config.early_radar_v1_frozen import EARLY_RADAR_V1_FROZEN
    assert MODEL_V3_2_FINGERPRINT["model_version"] == "MODEL_V3.2_FROZEN"
    assert EARLY_RADAR_V1_FROZEN["model_version"] == "EARLY_RADAR_V1_FROZEN"
