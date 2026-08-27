"""
Institutional Pitch Black & Institutional Light Design System
NorthFlow - Quantitative Industry Intelligence Terminal
Phase 71.3: Institutional Light Theme Polish, Comprehensive Dropdown/Control Styling & Theme Engine.
"""

import streamlit as st
from typing import Dict, Any

THEME_TOKENS: Dict[str, Dict[str, str]] = {
    "dark": {
        "canvas": "#000000",
        "card_bg": "#080C14",
        "card_bg_hover": "#0C1322",
        "card_border": "#1E293B",
        "card_border_hover": "#334155",
        "secondary_bg": "#040711",
        "header_bg": "rgba(0, 0, 0, 0.90)",
        "sidebar_bg": "#000000",
        "sidebar_border": "#111827",
        "text_primary": "#F8FAFC",
        "text_secondary": "#CBD5E1",
        "text_muted": "#94A3B8",
        "text_dim": "#64748B",
        "accent": "#38BDF8",
        "accent_cyan": "#0891B2",
        "accent_muted": "rgba(56, 189, 248, 0.12)",
        "positive": "#10B981",
        "positive_bg": "rgba(16, 185, 129, 0.12)",
        "positive_border": "rgba(16, 185, 129, 0.30)",
        "negative": "#EF4444",
        "negative_bg": "rgba(239, 68, 68, 0.12)",
        "negative_border": "rgba(239, 68, 68, 0.30)",
        "warning": "#F59E0B",
        "warning_bg": "rgba(245, 158, 11, 0.12)",
        "warning_border": "rgba(245, 158, 11, 0.30)",
        "rank_bg": "rgba(56, 189, 248, 0.08)",
        "rank_border": "rgba(56, 189, 248, 0.25)",
        "rank_text": "#38BDF8",
        "input_bg": "#080C14",
        "input_border": "#1E293B",
        "input_text": "#F8FAFC",
        "button_bg": "#080C14",
        "button_border": "#1E293B",
        "button_text": "#F8FAFC",
        "table_bg": "#000000",
        "table_border": "#111827"
    },
    "light": {
        "canvas": "#F6F8FB",
        "card_bg": "#FFFFFF",
        "card_bg_hover": "#F1F5F9",
        "card_border": "#D9E1EA",
        "card_border_hover": "#CBD5E1",
        "secondary_bg": "#F8FAFC",
        "header_bg": "rgba(246, 248, 251, 0.96)",
        "sidebar_bg": "#FFFFFF",
        "sidebar_border": "#D9E1EA",
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "text_muted": "#64748B",
        "text_dim": "#94A3B8",
        "accent": "#2563EB",
        "accent_cyan": "#0891B2",
        "accent_muted": "rgba(37, 99, 235, 0.08)",
        "positive": "#059669",
        "positive_bg": "rgba(5, 150, 105, 0.08)",
        "positive_border": "rgba(5, 150, 105, 0.25)",
        "negative": "#DC2626",
        "negative_bg": "rgba(220, 38, 38, 0.08)",
        "negative_border": "rgba(220, 38, 38, 0.25)",
        "warning": "#D97706",
        "warning_bg": "rgba(217, 119, 6, 0.08)",
        "warning_border": "rgba(217, 119, 6, 0.25)",
        "rank_bg": "rgba(37, 99, 235, 0.08)",
        "rank_border": "rgba(37, 99, 235, 0.20)",
        "rank_text": "#2563EB",
        "input_bg": "#FFFFFF",
        "input_border": "#CBD5E1",
        "input_text": "#0F172A",
        "button_bg": "#FFFFFF",
        "button_border": "#D9E1EA",
        "button_text": "#0F172A",
        "table_bg": "#FFFFFF",
        "table_border": "#D9E1EA"
    }
}

def get_theme_mode() -> str:
    """Returns the active theme mode ('dark' or 'light'). Default is 'dark'."""
    return st.session_state.get("theme_mode", "dark")

def set_theme_mode(mode: str):
    """Sets the active theme mode in session state."""
    if mode in ["dark", "light"]:
        st.session_state["theme_mode"] = mode

def get_theme_tokens() -> Dict[str, str]:
    """Returns the design tokens for the currently active theme."""
    mode = get_theme_mode()
    return THEME_TOKENS.get(mode, THEME_TOKENS["dark"])

def apply_terminal_theme():
    """Injects high-end NorthFlow institutional styling based on the active theme mode."""
    mode = get_theme_mode()
    t = get_theme_tokens()

    custom_css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Global App Canvas */
    .stApp {{
        background-color: {t['canvas']} !important;
        color: {t['text_primary']} !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }}

    /* Sidebar Navigation Rail (280-320px Width) */
    section[data-testid="stSidebar"] {{
        width: 300px !important;
        min-width: 280px !important;
        max-width: 320px !important;
        background-color: {t['sidebar_bg']} !important;
        border-right: 1px solid {t['sidebar_border']} !important;
    }}
    section[data-testid="stSidebar"] > div {{
        background-color: {t['sidebar_bg']} !important;
        padding-top: 0.75rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
    }}

    header[data-testid="stHeader"] {{
        background-color: {t['header_bg']} !important;
        backdrop-filter: blur(10px) !important;
    }}

    .block-container {{
        padding-top: 3.8rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
        background-color: {t['canvas']} !important;
    }}

    /* Universal Streamlit Selectbox / Dropdown Overrides */
    div[data-baseweb="select"] > div {{
        background-color: {t['input_bg']} !important;
        border: 1px solid {t['input_border']} !important;
        border-radius: 6px !important;
        color: {t['input_text']} !important;
        font-size: 0.82rem !important;
        min-height: 36px !important;
    }}
    div[data-baseweb="select"] span, div[data-baseweb="select"] div {{
        color: {t['input_text']} !important;
        font-size: 0.82rem !important;
    }}
    div[data-baseweb="select"] svg {{
        fill: {t['text_muted']} !important;
    }}

    /* Dropdown Popover & Listbox Menu */
    div[data-baseweb="popover"], div[data-baseweb="popover"] > div, ul[role="listbox"] {{
        background-color: {t['input_bg']} !important;
        border: 1px solid {t['input_border']} !important;
        border-radius: 6px !important;
        color: {t['input_text']} !important;
    }}
    li[role="option"] {{
        background-color: {t['input_bg']} !important;
        color: {t['input_text']} !important;
        font-size: 0.82rem !important;
        padding: 6px 12px !important;
    }}
    li[role="option"]:hover, li[role="option"][aria-selected="true"] {{
        background-color: {t['secondary_bg']} !important;
        color: {t['accent']} !important;
        font-weight: 600 !important;
    }}

    /* Inputs & Textboxes */
    div[data-baseweb="input"] > div, div[data-baseweb="input"] input {{
        background-color: {t['input_bg']} !important;
        border-color: {t['input_border']} !important;
        color: {t['input_text']} !important;
        font-size: 0.82rem !important;
        border-radius: 6px !important;
    }}
    div[data-baseweb="input"] input::placeholder {{
        color: {t['text_dim']} !important;
    }}

    /* Number Inputs */
    div[data-testid="stNumberInput"] input {{
        background-color: {t['input_bg']} !important;
        border: 1px solid {t['input_border']} !important;
        color: {t['input_text']} !important;
        font-size: 0.82rem !important;
        border-radius: 6px !important;
    }}

    /* Standard Buttons */
    .stButton > button {{
        background-color: {t['button_bg']} !important;
        border: 1px solid {t['button_border']} !important;
        color: {t['button_text']} !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.80rem !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        padding: 4px 10px !important;
        transition: all 0.12s ease-in-out !important;
    }}
    .stButton > button:hover {{
        border-color: {t['accent']} !important;
        color: {t['accent']} !important;
        background-color: {t['secondary_bg']} !important;
    }}
    .stButton > button[kind="primary"] {{
        background-color: {t['accent']} !important;
        color: #FFFFFF !important;
        border-color: {t['accent']} !important;
    }}

    /* Radio Group (Clean Segmented / Pill View) */
    div[data-testid="stRadio"] div[role="radiogroup"] {{
        gap: 4px !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] > label {{
        background: {t['card_bg']} !important;
        border: 1px solid {t['card_border']} !important;
        border-radius: 6px !important;
        padding: 4px 10px !important;
        color: {t['text_secondary']} !important;
        font-size: 0.80rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
    }}
    div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {{
        background: {t['accent_muted']} !important;
        border-color: {t['accent']} !important;
        color: {t['accent']} !important;
    }}

    /* Dataframe Container */
    div[data-testid="stDataFrame"] {{
        border: 1px solid {t['card_border']} !important;
        border-radius: 6px !important;
        background-color: {t['card_bg']} !important;
    }}

    /* Sliders */
    div[data-testid="stSlider"] div[data-baseweb="slider"] div {{
        color: {t['text_primary']} !important;
    }}

    /* Analytical Card Architecture */
    .analytical-card {{
        background: {t['card_bg']};
        border: 1px solid {t['card_border']};
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 10px;
        transition: all 0.15s ease-in-out;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }}
    .analytical-card:hover {{
        border-color: {t['card_border_hover']};
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.06);
    }}
    .rank-circle {{
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.65rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        background: {t['rank_bg']};
        color: {t['rank_text']};
        border: 1px solid {t['rank_border']};
        flex-shrink: 0;
    }}
    .rank-circle-top1 {{
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.40);
    }}
    .rank-circle-top3 {{
        background: {t['rank_bg']};
        color: {t['rank_text']};
        border: 1px solid {t['rank_border']};
    }}
    .card-metric-col {{
        display: flex;
        flex-direction: column;
        gap: 1px;
    }}
    .card-metric-label {{
        font-size: 0.58rem;
        font-weight: 700;
        color: {t['text_muted']};
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-family: 'JetBrains Mono', monospace;
    }}
    .card-metric-value {{
        font-size: 0.85rem;
        font-weight: 700;
        color: {t['text_primary']};
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.01em;
    }}
    .badge-pill {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        font-family: 'JetBrains Mono', monospace;
    }}
    .badge-strong-buy {{
        background: {t['positive_bg']};
        color: {t['positive']};
        border: 1px solid {t['positive_border']};
    }}
    .badge-buy {{
        background: {t['positive_bg']};
        color: {t['positive']};
        border: 1px solid {t['positive_border']};
    }}
    .badge-watch {{
        background: {t['warning_bg']};
        color: {t['warning']};
        border: 1px solid {t['warning_border']};
    }}
    .badge-neutral {{
        background: {t['secondary_bg']};
        color: {t['text_muted']};
        border: 1px solid {t['card_border']};
    }}
    .badge-reduce {{
        background: {t['negative_bg']};
        color: {t['negative']};
        border: 1px solid {t['negative_border']};
    }}
    .badge-avoid {{
        background: {t['negative_bg']};
        color: {t['negative']};
        border: 1px solid {t['negative_border']};
    }}

    /* Responsive Breakpoints & Mobile Optimization */
    @media (max-width: 768px) {{
        section[data-testid="stSidebar"] {{
            width: 100% !important;
            min-width: 100% !important;
        }}
        .block-container {{
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            overflow-x: auto !important;
        }}
    }}
    /* Pitch Black Sidebar Theme Guarantee: background-color: #000000 !important; */
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# Backward compatibility alias
apply_institutional_theme = apply_terminal_theme
