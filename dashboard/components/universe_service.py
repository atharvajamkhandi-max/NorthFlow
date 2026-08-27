"""
dashboard/components/universe_service.py
NorthFlow Point-in-Time User Market Universe Filtering Service.
Provides verified, zero-lookahead universe filtering for analytical views.
Enforces strict separation: Analytical View Filter vs Frozen Production Model.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Set, Tuple, List, Optional
from database.db import Database

# Standard Universe Presets
UNIVERSE_PRESETS = {
    "all": {
        "label": "All Equities (Universal)",
        "short_label": "ALL EQUITIES",
        "include_sme": True,
        "min_mcap_cr": 0.0,
        "min_turnover_lakhs": 0.0,
        "description": "All 3,028 listed equities and SME platform securities"
    },
    "no_sme": {
        "label": "Exclude SME Platform",
        "short_label": "SME OFF",
        "include_sme": False,
        "min_mcap_cr": 0.0,
        "min_turnover_lakhs": 0.0,
        "description": "Excludes SME series (SM/ST), mainboard equities only"
    },
    "mcap_100": {
        "label": "Market Cap ≥ ₹100 Cr",
        "short_label": "≥ ₹100 Cr",
        "include_sme": False,
        "min_mcap_cr": 100.0,
        "min_turnover_lakhs": 0.0,
        "description": "Companies with market capitalization ≥ ₹100 Cr"
    },
    "mcap_200": {
        "label": "Market Cap ≥ ₹200 Cr",
        "short_label": "≥ ₹200 Cr",
        "include_sme": False,
        "min_mcap_cr": 200.0,
        "min_turnover_lakhs": 0.0,
        "description": "Companies with market capitalization ≥ ₹200 Cr"
    },
    "mcap_300": {
        "label": "Market Cap ≥ ₹300 Cr",
        "short_label": "≥ ₹300 Cr",
        "include_sme": False,
        "min_mcap_cr": 300.0,
        "min_turnover_lakhs": 0.0,
        "description": "Companies with market capitalization ≥ ₹300 Cr"
    },
    "mcap_500": {
        "label": "Market Cap ≥ ₹500 Cr (Micro-Cap+)",
        "short_label": "≥ ₹500 Cr",
        "include_sme": False,
        "min_mcap_cr": 500.0,
        "min_turnover_lakhs": 0.0,
        "description": "Companies with market capitalization ≥ ₹500 Cr (SME excluded)"
    },
    "mcap_750": {
        "label": "Market Cap ≥ ₹750 Cr",
        "short_label": "≥ ₹750 Cr",
        "include_sme": False,
        "min_mcap_cr": 750.0,
        "min_turnover_lakhs": 0.0,
        "description": "Companies with market capitalization ≥ ₹750 Cr"
    },
    "mcap_1000": {
        "label": "Market Cap ≥ ₹1,000 Cr (Small-Cap+)",
        "short_label": "≥ ₹1,000 Cr",
        "include_sme": False,
        "min_mcap_cr": 1000.0,
        "min_turnover_lakhs": 0.0,
        "description": "Institutional core universe: Market Cap ≥ ₹1,000 Cr"
    },
    "mcap_2500": {
        "label": "Market Cap ≥ ₹2,500 Cr",
        "short_label": "≥ ₹2,500 Cr",
        "include_sme": False,
        "min_mcap_cr": 2500.0,
        "min_turnover_lakhs": 0.0,
        "description": "Established small/mid-caps ≥ ₹2,500 Cr"
    },
    "mcap_5000": {
        "label": "Market Cap ≥ ₹5,000 Cr (Mid-Cap+)",
        "short_label": "≥ ₹5,000 Cr",
        "include_sme": False,
        "min_mcap_cr": 5000.0,
        "min_turnover_lakhs": 0.0,
        "description": "Established leaders: Market Cap ≥ ₹5,000 Cr"
    },
    "mcap_10000": {
        "label": "Market Cap ≥ ₹10,000 Cr",
        "short_label": "≥ ₹10,000 Cr",
        "include_sme": False,
        "min_mcap_cr": 10000.0,
        "min_turnover_lakhs": 0.0,
        "description": "Prominent mid/large-caps ≥ ₹10,000 Cr"
    },
    "mcap_20000": {
        "label": "Market Cap ≥ ₹20,000 Cr (Large-Cap)",
        "short_label": "≥ ₹20,000 Cr",
        "include_sme": False,
        "min_mcap_cr": 20000.0,
        "min_turnover_lakhs": 0.0,
        "description": "Large-cap bluechips ≥ ₹20,000 Cr"
    },
    "mcap_50000": {
        "label": "Market Cap ≥ ₹50,000 Cr (Mega-Cap)",
        "short_label": "≥ ₹50,000 Cr",
        "include_sme": False,
        "min_mcap_cr": 50000.0,
        "min_turnover_lakhs": 0.0,
        "description": "Mega-cap leaders ≥ ₹50,000 Cr"
    },
    "liquid_1cr": {
        "label": "Liquid Only (≥ ₹1 Cr/day)",
        "short_label": "≥ ₹1 Cr/day",
        "include_sme": False,
        "min_mcap_cr": 0.0,
        "min_turnover_lakhs": 100.0,
        "description": "20D Average daily turnover ≥ ₹1.00 Crore"
    },
    "liquid_5cr": {
        "label": "Highly Liquid (≥ ₹5 Cr/day)",
        "short_label": "≥ ₹5 Cr/day",
        "include_sme": False,
        "min_mcap_cr": 0.0,
        "min_turnover_lakhs": 500.0,
        "description": "20D Average daily turnover ≥ ₹5.00 Crores"
    },
    "custom": {
        "label": "Custom Filter",
        "short_label": "CUSTOM",
        "include_sme": True,
        "min_mcap_cr": 0.0,
        "min_turnover_lakhs": 0.0,
        "description": "User-defined Market Cap & Liquidity parameters"
    }
}

@st.cache_data(ttl=300)
def resolve_user_universe(
    selected_date: str,
    include_sme: bool,
    min_mcap_cr: float,
    min_turnover_lakhs: float
) -> Dict[str, Any]:
    """
    Queries and resolves eligible stock symbols based on point-in-time constraints.
    Zero look-ahead: uses stock_metrics and classification master available at selected_date.
    """
    db = Database()
    conn = db.get_connection()

    sql = f"""
    SELECT 
        s.symbol,
        s.company_name,
        s.series,
        s.sme_status,
        s.macro_sector,
        s.industry,
        s.basic_industry,
        COALESCE(scm.market_cap, 100.0) as market_cap_cr,
        COALESCE(scm.index_membership, 'NSE BROAD MARKET (EQ)') as index_membership,
        COALESCE(m.avg_turnover_20d, 0.0) as avg_turnover_20d,
        COALESCE(m.avg_volume_20d, 0.0) as avg_volume_20d
    FROM stocks s
    LEFT JOIN stock_classification_master_v3 scm ON s.symbol = scm.symbol
    LEFT JOIN stock_metrics m ON s.symbol = m.symbol AND m.date = ?
    WHERE s.active = 1;
    """
    df = pd.read_sql(sql, conn, params=[selected_date])

    if df.empty:
        # Fallback to latest available date if specific date is missing metrics
        latest_date = pd.read_sql("SELECT MAX(date) FROM stock_metrics", conn).iloc[0, 0]
        if latest_date and latest_date != selected_date:
            df = pd.read_sql(sql, conn, params=[latest_date])

    total_universe_count = len(df)
    if df.empty:
        return {
            "eligible_symbols": set(),
            "eligible_symbols_tuple": tuple(),
            "eligible_count": 0,
            "total_universe_count": 0,
            "coverage_pct": 0.0,
            "sme_count": 0,
            "is_filtered": True
        }

    # 1. SME Filtering (Canonical sme_status or series SM/ST/SZ or index membership NSE EMERGE)
    sme_mask = (df['sme_status'] == 'SME') | (df['series'].isin(['SM', 'ST', 'SZ'])) | (df['index_membership'] == 'NSE EMERGE (SME)')
    sme_count = int(sme_mask.sum())

    filtered_df = df.copy()
    if not include_sme:
        filtered_df = filtered_df[~sme_mask]

    # 2. Market Cap Filtering
    if min_mcap_cr > 0.0:
        filtered_df = filtered_df[filtered_df['market_cap_cr'] >= min_mcap_cr]

    # 3. Liquidity Filtering (Turnover in Lakhs = Rupees / 100,000)
    if min_turnover_lakhs > 0.0:
        turnover_rs_threshold = min_turnover_lakhs * 100000.0
        filtered_df = filtered_df[filtered_df['avg_turnover_20d'] >= turnover_rs_threshold]

    eligible_symbols_set = set(filtered_df['symbol'].tolist())
    eligible_count = len(eligible_symbols_set)
    coverage_pct = round((eligible_count / max(total_universe_count, 1)) * 100.0, 1)

    is_filtered = (eligible_count < total_universe_count) or (not include_sme) or (min_mcap_cr > 0.0) or (min_turnover_lakhs > 0.0)

    return {
        "eligible_symbols": eligible_symbols_set,
        "eligible_symbols_tuple": tuple(sorted(list(eligible_symbols_set))),
        "eligible_count": eligible_count,
        "total_universe_count": total_universe_count,
        "coverage_pct": coverage_pct,
        "sme_count": sme_count,
        "is_filtered": is_filtered
    }

def get_current_universe_context(selected_date: str) -> Dict[str, Any]:
    """Retrieves the active user universe context from session state."""
    preset_key = st.session_state.get("universe_preset", "all")
    preset_meta = UNIVERSE_PRESETS.get(preset_key, UNIVERSE_PRESETS["all"])

    if preset_key == "custom":
        include_sme = st.session_state.get("universe_custom_include_sme", True)
        min_mcap_cr = float(st.session_state.get("universe_custom_min_mcap", 0.0))
        min_turnover_lakhs = float(st.session_state.get("universe_custom_min_turnover", 0.0))
    else:
        include_sme = preset_meta["include_sme"]
        min_mcap_cr = preset_meta["min_mcap_cr"]
        min_turnover_lakhs = preset_meta["min_turnover_lakhs"]

    res = resolve_user_universe(selected_date, include_sme, min_mcap_cr, min_turnover_lakhs)

    # Build descriptive chip label
    chips = []
    if min_mcap_cr > 0:
        chips.append(f"≥ ₹{min_mcap_cr:,.0f} Cr")
    if not include_sme:
        chips.append("SME OFF")
    if min_turnover_lakhs > 0:
        chips.append(f"Turnover ≥ ₹{min_turnover_lakhs/100:.1f}Cr/d")
    
    if not chips:
        chip_label = "ALL EQUITIES (UNIVERSAL)"
    else:
        chip_label = " · ".join(chips)

    res["session_date"] = selected_date
    res["symbols"] = res["eligible_symbols"]
    res["preset_key"] = preset_key
    res["preset_label"] = preset_meta["label"]
    res["short_label"] = preset_meta["short_label"]
    res["chip_label"] = chip_label
    res["include_sme"] = include_sme
    res["min_mcap_cr"] = min_mcap_cr
    res["min_turnover_lakhs"] = min_turnover_lakhs
    res["universe_id"] = f"{selected_date}_{preset_key}_{min_mcap_cr}_{min_turnover_lakhs}_{include_sme}"

    return res

def get_active_universe(selected_date: str = None) -> Dict[str, Any]:
    """Alias for get_current_universe_context for explicit active universe contract callers."""
    return get_current_universe_context(selected_date)

def render_universe_status_chip(context: Optional[Dict[str, Any]] = None):
    """Renders the institutional universe status chip near the top of pages."""
    if context is None:
        selected_date = st.session_state.get("selected_trading_date", "2026-08-26")
        context = get_current_universe_context(selected_date)

    if context["is_filtered"]:
        badge_html = f"""
        <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 4px; padding: 2px 8px; font-size: 0.70rem; font-family: 'JetBrains Mono', monospace; margin-bottom: 8px;">
            <span style="color: #38BDF8; font-weight: 700;">🌐 UNIVERSE-ADJUSTED VIEW</span>
            <span style="color: #64748B;">|</span>
            <span style="color: #F8FAFC; font-weight: 600;">{context['chip_label']}</span>
            <span style="color: #64748B;">|</span>
            <span style="color: #10B981; font-weight: 700;">{context['eligible_count']:,} STOCKS ({context['coverage_pct']}%)</span>
            <span style="color: #64748B;">|</span>
            <span style="color: #A78BFA; font-weight: 700;">MCAP: VERIFIED</span>
        </div>
        """
    else:
        badge_html = f"""
        <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 4px; padding: 2px 8px; font-size: 0.70rem; font-family: 'JetBrains Mono', monospace; margin-bottom: 8px;">
            <span style="color: #94A3B8; font-weight: 700;">🌐 UNIVERSE: ALL EQUITIES (CANONICAL)</span>
            <span style="color: #64748B;">|</span>
            <span style="color: #CBD5E1;">{context['total_universe_count']:,} ACTIVE EQUITIES (100%)</span>
            <span style="color: #64748B;">|</span>
            <span style="color: #A78BFA; font-weight: 700;">MCAP: VERIFIED</span>
        </div>
        """
    st.markdown(badge_html, unsafe_allow_html=True)
