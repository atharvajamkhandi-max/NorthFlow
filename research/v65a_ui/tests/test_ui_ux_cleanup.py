"""
research/v65a_ui/tests/test_ui_ux_cleanup.py
Isolated unit tests for Phase 65A NorthFlow Website UI/UX Cleanup.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LIVE_DIR = BASE_DIR / "research" / "live_forward"

def test_1_theme_responsive_css_rules_present():
    theme_file = BASE_DIR / "dashboard" / "components" / "theme.py"
    assert theme_file.exists()
    with open(theme_file, "r", encoding="utf-8") as f:
        theme_content = f.read()
    assert "@media (max-width: 768px)" in theme_content
    assert "overflow-x: auto" in theme_content
    assert "padding-top: 3.8rem !important;" in theme_content

def test_2_live_validation_ui_exists_and_loads_canonical_artifacts():
    d_file = BASE_DIR / "dashboard" / "live_forward_validation_ui.py"
    assert d_file.exists()
    from dashboard.live_forward_validation_ui import _load_json_safe, _load_csv_safe
    scorecard = _load_json_safe(LIVE_DIR / "scorecards" / "cumulative_live_scorecard.json")
    df_p = _load_csv_safe(LIVE_DIR / "ledger" / "live_predictions.csv")
    assert scorecard is not None
    assert df_p is not None

def test_3_production_immutability_checksums_match():
    pre_file = BASE_DIR / "research" / "v65a_ui" / "safety" / "checksums_preflight.json"
    post_file = BASE_DIR / "research" / "v65a_ui" / "safety" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
