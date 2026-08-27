"""
NSE Trading Session Calendar & Date-Aware Navigation Component.
Phase 71.3: Dynamic theme-aware session selector and quick navigation buttons.
"""

import datetime
import streamlit as st
import pandas as pd
import textwrap
from typing import List, Dict, Any, Tuple, Optional
from database.db import Database
from dashboard.components.theme import get_theme_tokens

@st.cache_data(ttl=300)
def get_available_nse_sessions_cached() -> List[str]:
    """Retrieves all distinct trading dates available in SQLite sorted chronologically."""
    db = Database()
    dates = db.get_existing_price_dates()
    if not dates:
        return []
    return sorted(list(set(dates)))

def get_available_nse_sessions(db: Optional[Database] = None) -> List[str]:
    """Retrieves all distinct trading dates available in SQLite."""
    return get_available_nse_sessions_cached()

def get_session_maturity_status(selected_date: str, all_sessions: List[str]) -> Dict[str, Any]:
    """Determines forward return maturity based on elapsed actual NSE trading sessions."""
    if not all_sessions:
        return {'5D': False, '10D': False, '20D': False, '30D': False, 'elapsed_trading_sessions': 0, 'is_latest': True, 'session_number': 1, 'total_sessions': 1}

    if selected_date not in all_sessions:
        selected_date = all_sessions[-1]
    
    idx = all_sessions.index(selected_date)
    elapsed = len(all_sessions) - 1 - idx
    
    return {
        '5D': elapsed >= 5,
        '10D': elapsed >= 10,
        '20D': elapsed >= 20,
        '30D': elapsed >= 30,
        'elapsed_trading_sessions': elapsed,
        'is_latest': (idx == len(all_sessions) - 1),
        'session_number': idx + 1,
        'total_sessions': len(all_sessions)
    }

def _set_trading_session(target_date_str: str):
    """Callback for quick navigation buttons."""
    st.session_state["selected_trading_date"] = target_date_str

def render_trading_session_calendar(db: Optional[Database] = None) -> str:
    t = get_theme_tokens()
    if db is None:
        db = Database()

    all_sessions = get_available_nse_sessions(db)
    if not all_sessions:
        st.sidebar.warning("No trading sessions found in database.")
        return datetime.date.today().strftime("%Y-%m-%d")

    first_session = all_sessions[0]
    latest_session = all_sessions[-1]

    if "selected_trading_date" not in st.session_state or st.session_state["selected_trading_date"] not in all_sessions:
        st.session_state["selected_trading_date"] = latest_session

    curr_selected_str = st.session_state["selected_trading_date"]
    curr_idx = all_sessions.index(curr_selected_str)
    curr_dt = datetime.datetime.strptime(curr_selected_str, "%Y-%m-%d").date()

    st.sidebar.markdown(f"""
    <div style="font-size: 0.60rem; font-weight: 800; color: {t['text_dim']}; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 2px;">
        SESSION DATE
    </div>
    """, unsafe_allow_html=True)

    reversed_sessions = list(reversed(all_sessions))
    formatted_options = [f"{datetime.datetime.strptime(s, '%Y-%m-%d').strftime('%d %b %Y')} ({datetime.datetime.strptime(s, '%Y-%m-%d').strftime('%A')})" for s in reversed_sessions]
    session_map = dict(zip(formatted_options, reversed_sessions))
    curr_formatted = f"{curr_dt.strftime('%d %b %Y')} ({curr_dt.strftime('%A')})"

    curr_fmt_idx = formatted_options.index(curr_formatted) if curr_formatted in formatted_options else 0
    selected_fmt = st.sidebar.selectbox(
        "Select Session",
        options=formatted_options,
        index=curr_fmt_idx,
        key="sb_session_select",
        label_visibility="collapsed"
    )
    chosen_date = session_map[selected_fmt]
    st.session_state["selected_trading_date"] = chosen_date

    # Quick Navigation Buttons
    q1, q2, q3, q4 = st.sidebar.columns(4)
    with q1:
        st.button("First", help="Jump to earliest session", disabled=(curr_idx <= 0), on_click=_set_trading_session, args=(first_session,), key="btn_first_sess", use_container_width=True)
    with q2:
        prev_sess = all_sessions[max(0, curr_idx - 1)]
        st.button("Prev", help="Step back 1 session", disabled=(curr_idx <= 0), on_click=_set_trading_session, args=(prev_sess,), key="btn_prev_sess", use_container_width=True)
    with q3:
        next_sess = all_sessions[min(len(all_sessions) - 1, curr_idx + 1)]
        st.button("Next", help="Step forward 1 session", disabled=(curr_idx >= len(all_sessions) - 1), on_click=_set_trading_session, args=(next_sess,), key="btn_next_sess", use_container_width=True)
    with q4:
        st.button("Latest", help="Jump to latest session", disabled=(curr_idx >= len(all_sessions) - 1), on_click=_set_trading_session, args=(latest_session,), key="btn_latest_sess", use_container_width=True)

    st.sidebar.markdown(f"<div style='border-bottom: 1px solid {t['sidebar_border']}; margin: 6px 0;'></div>", unsafe_allow_html=True)
    return chosen_date
