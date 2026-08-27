"""
research/v64_ui/tests/test_live_forward_dashboard.py
Isolated unit tests for Phase 64 Safe Website Live-Forward Shadow Dashboard Integration.
"""
import pytest
import json
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
LIVE_DIR = BASE_DIR / "research" / "live_forward"

def test_1_dashboard_module_and_app_navigation_exist():
    d_file = BASE_DIR / "dashboard" / "live_forward_validation_ui.py"
    app_file = BASE_DIR / "app.py"
    assert d_file.exists()
    with open(app_file, "r", encoding="utf-8") as f:
        app_content = f.read()
    assert "🔮 Live Forward Validation (Shadow)" in app_content
    assert "render_live_forward_validation_ui" in app_content

def test_2_canonical_artifacts_loaded_correctly():
    from dashboard.live_forward_validation_ui import _load_json_safe, _load_csv_safe
    op = _load_json_safe(LIVE_DIR / "monitoring" / "operational_status.json")
    scorecard = _load_json_safe(LIVE_DIR / "scorecards" / "cumulative_live_scorecard.json")
    df_p = _load_csv_safe(LIVE_DIR / "ledger" / "live_predictions.csv")
    assert op is not None
    assert scorecard is not None
    assert df_p is not None
    assert len(df_p) == 1196

def test_3_safe_degradation_on_missing_or_corrupted_file():
    from dashboard.live_forward_validation_ui import _load_json_safe, _load_csv_safe
    fake_path = Path("fake_non_existent_file.json")
    assert _load_json_safe(fake_path) is None
    assert _load_csv_safe(fake_path) is None

def test_4_promotion_gate_displayed_as_locked():
    from dashboard.live_forward_validation_ui import _load_json_safe
    gate = _load_json_safe(LIVE_DIR / "promotion_gate" / "promotion_status.json")
    assert gate["promotion_status"] == "LOCKED"
    assert gate["production_deployment_allowed"] == False

def test_5_production_immutability_checksums_match():
    pre_file = BASE_DIR / "research" / "v64_ui" / "safety" / "checksums_preflight.json"
    post_file = BASE_DIR / "research" / "v64_ui" / "safety" / "checksums_postflight.json"
    assert pre_file.exists()
    assert post_file.exists()
    with open(pre_file, "r") as f1, open(post_file, "r") as f2:
        pre = json.load(f1)
        post = json.load(f2)
    assert pre == post
