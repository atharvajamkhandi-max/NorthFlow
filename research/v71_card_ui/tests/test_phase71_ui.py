"""
research/v71_card_ui/tests/test_phase71_ui.py
Automated Unit & Integration Tests for Phase 71.1 Premium Analytical Card UI & Visual System.
"""
import pytest
import pandas as pd
import numpy as np
import ast
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

def test_1_theme_token_engine_and_switching():
    from dashboard.components.theme import THEME_TOKENS, get_theme_mode, set_theme_mode, get_theme_tokens
    
    set_theme_mode("dark")
    assert get_theme_mode() == "dark"
    t_dark = get_theme_tokens()
    assert t_dark["canvas"] == "#000000"
    assert t_dark["text_primary"] == "#F8FAFC"
    assert "rank_bg" in t_dark
    
    set_theme_mode("light")
    assert get_theme_mode() == "light"
    t_light = get_theme_tokens()
    assert t_light["canvas"] in ["#F6F8FB", "#F8FAFC"]
    assert t_light["text_primary"] == "#0F172A"
    assert t_light["card_bg"] == "#FFFFFF"
    
    set_theme_mode("dark")
    assert get_theme_mode() == "dark"

def test_2_analytical_card_rendering_and_zero_html_leakage():
    from dashboard.components.analytical_card import render_analytical_card, generate_mini_sparkbar_svg
    from dashboard.components.theme import get_theme_tokens
    
    t = get_theme_tokens()
    svg = generate_mini_sparkbar_svg(25.0, 50.0, 75.0, 90.0, t)
    assert "<svg" in svg
    assert "</svg>" in svg
    
    card_html = render_analytical_card(
        rank=1,
        title="Wires & Cables",
        subtitle="15 stocks · ELECTRICAL",
        action="STRONG BUY",
        trend="Strong Bullish",
        strength=88.5,
        exp_return_20d=14.2,
        confidence=72.0,
        risk=28.0,
        breadth_50=80.0,
        constituent_count=15
    )
    
    # 1. Zero markdown code-block leakage checks
    assert card_html.startswith("<div"), f"HTML starts with invalid character: {repr(card_html[:20])}"
    assert not card_html.startswith(" "), "HTML has leading whitespace indentation!"
    for line in card_html.splitlines():
        if line.startswith("    ") and ("<div" in line or "<span" in line):
            raise AssertionError(f"4-space indented HTML tag detected: {repr(line)}")
            
    # 2. Key information checks
    assert "#01" in card_html
    assert "Wires & Cables" in card_html
    assert "STRONG BUY" in card_html
    assert "88.5" in card_html
    assert "+14.2%" in card_html

def test_3_analytical_card_grid_generation():
    from dashboard.components.analytical_card import render_analytical_card_grid
    
    df_sample = pd.DataFrame([
        {
            "Rank": 1, "entity_name": "AI Compute Hardware", "macro_sector": "Information Technology",
            "current_strength": 92.0, "exp_return_20d": 18.5, "breadth_50": 85.0,
            "confidence_score": 80.0, "risk_score": 20.0, "constituent_count": 8,
            "final_action": "STRONG BUY", "trend_rating": "Strong Bullish"
        },
        {
            "Rank": 2, "entity_name": "Switchgear & Power", "macro_sector": "Capital Goods",
            "current_strength": 86.4, "exp_return_20d": 12.1, "breadth_50": 75.0,
            "confidence_score": 75.0, "risk_score": 25.0, "constituent_count": 12,
            "final_action": "BUY", "trend_rating": "Bullish"
        }
    ])
    
    render_analytical_card_grid(df_sample, max_cards=2, columns=2)
    assert len(df_sample) == 2

def test_4_all_12_navigation_routes_preserved():
    app_file = BASE_DIR / "app.py"
    with open(app_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    expected_routes = [
        "🎯 Industry Intelligence",
        "🔮 Live Forward Validation (Shadow)",
        "📡 Early Sector Radar (Shadow)",
        "🧠 Historical Decision Memory",
        "📈 Market Overview",
        "🌊 Industry Flow",
        "🚀 Emerging Rotations",
        "🔄 Rotation Map",
        "🏭 Industries Explorer",
        "⚡ Stock Screener",
        "🛡️ Data Health",
        "⚙️ Settings & Methodology"
    ]
    for r in expected_routes:
        assert r in content, f"Route {r} missing from app.py navigation!"

def test_5_production_immutability_checksums():
    import hashlib
    def get_sha256(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            while c := f.read(65536):
                h.update(c)
        return h.hexdigest()

    frozen_model = BASE_DIR / "config" / "model_v3_2_frozen.py"
    final_pred = BASE_DIR / "research" / "final_v3" / "results" / "final_predictions.csv"
    live_pred = BASE_DIR / "research" / "live_forward" / "ledger" / "live_predictions.csv"
    live_hashes = BASE_DIR / "research" / "live_forward" / "ledger" / "live_hashes.csv"
    promotion_status = BASE_DIR / "research" / "live_forward" / "promotion_gate" / "promotion_status.json"
    decision_ledger = BASE_DIR / "data" / "decision_ledger.db"
    
    assert get_sha256(frozen_model) == "e350e9209960357d75668ff3dc9fb742162525169ae1f19d7fb7b681beadc756"
    assert get_sha256(final_pred) == "52019b780e8b9d714e8f926063dce725541b27335dec47b7f6e66346520bca6b"
    assert get_sha256(live_pred) == "7950580952b7d3e4d082aeb2c8b48ed892fbe9ce2487d0755255cce81977136e"
    assert get_sha256(live_hashes) == "0010c55813170804e62726ce458ac78cee0394b8995b9f3d2bd8066014c0ca43"
    assert get_sha256(promotion_status) == "e9761f0b27853f1e2d3635dbe11a36a859b2dee899a1aeb6a15a8f39c1575fa3"
    assert get_sha256(decision_ledger) == "2a3f7046e8cf072a959c044ddd879a61720deb049eb7ff5cc16703acdf8f7696"
