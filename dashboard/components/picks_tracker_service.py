"""
High-Conviction Multi-Horizon Quality Picks & Trade Lifecycle Ledger Service.
NorthFlow Quantitative Trading & Accountability Engine.
Zero-Compulsion Rule: Only outputs setups meeting institutional pattern, volume, and quant thresholds.
"""

import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import textwrap
from typing import Dict, Any, List, Optional
from database.db import Database
from dashboard.components.theme import get_theme_tokens
from analytics.canonical_v3_2_service import get_canonical_stock_quant_score, get_canonical_hierarchy_quant_scores

def compute_quality_picks_for_session(selected_date: str, horizon: str = "DAILY") -> pd.DataFrame:
    """
    Extracts high-conviction quality setups filtered by strict pattern, volume, and quant rules.
    Horizons: 'DAILY' (1-3D), 'WEEKLY' (1-2W), 'MONTHLY' (1-3M), 'LONG_TERM' (6-12M).
    """
    df_stocks = get_canonical_stock_quant_score(selected_date)
    if df_stocks.empty:
        return pd.DataFrame()
    
    # 1. Base Quality Gate (Only STRONG BUY / BUY with solid strength)
    base_pool = df_stocks[
        (df_stocks['final_action'].isin(['STRONG BUY', 'BUY'])) &
        (df_stocks['stock_strength_score'] >= 65.0) &
        (df_stocks['above_50ema'] == 1) &
        (df_stocks['close_price'] >= 20.0)
    ].copy()
    
    if base_pool.empty:
        return pd.DataFrame()

    # 2. Horizon-Specific Setup Identification
    if horizon == "DAILY":
        # Daily Momentum: Volume surge >= 1.8x, RS_5D > 0, 20D Breakout or strong 1D momentum
        picks = base_pool[
            (base_pool['volume_ratio'] >= 1.8) &
            (base_pool['rs_5d'] > 0.0) &
            ((base_pool['is_breakout_20d'] == 1) | (base_pool['return_1d'] >= 2.0))
        ].copy()
        picks['horizon_label'] = "⚡ Daily Intraday / Momentum (1-3 Days)"
        picks['target_1_pct'] = 4.0
        picks['target_2_pct'] = 8.0
        picks['stop_loss_pct'] = -2.5
        picks['setup_type'] = np.where(picks['is_breakout_20d'] == 1, "20D Volume Breakout", "High-Volume Momentum Surge")
        picks['sort_key'] = picks['volume_ratio'] * picks['stock_strength_score']

    elif horizon == "WEEKLY":
        # Weekly Swing: Solid RS_20D, above 20EMA, moderate to high volume >= 1.2x
        picks = base_pool[
            (base_pool['above_20ema'] == 1) &
            (base_pool['rs_20d'] >= 2.0) &
            (base_pool['volume_ratio'] >= 1.2)
        ].copy()
        picks['horizon_label'] = "📅 Weekly Swing (1-2 Weeks)"
        picks['target_1_pct'] = 8.0
        picks['target_2_pct'] = 15.0
        picks['stop_loss_pct'] = -4.5
        picks['setup_type'] = np.where(picks['return_5d'] >= 3.0, "Multi-Day Trend Continuation", "20-EMA Pullback & Accumulation")
        picks['sort_key'] = picks['rs_20d'] + (picks['stock_strength_score'] * 0.5)

    elif horizon == "MONTHLY":
        # Monthly Position: High strength >= 75, RS_20D >= 5.0, top industry leadership
        picks = base_pool[
            (base_pool['stock_strength_score'] >= 75.0) &
            (base_pool['rs_20d'] >= 5.0)
        ].copy()
        picks['horizon_label'] = "🗓️ Monthly Position (1-3 Months)"
        picks['target_1_pct'] = 18.0
        picks['target_2_pct'] = 30.0
        picks['stop_loss_pct'] = -7.5
        picks['setup_type'] = "Structural Industry Outperformance"
        picks['sort_key'] = picks['stock_strength_score']

    else:  # LONG_TERM
        # Long-Term Compounder: Elite quant score >= 80, consistent leader, above all moving averages
        picks = base_pool[
            (base_pool['stock_strength_score'] >= 80.0) &
            (base_pool['above_20ema'] == 1) &
            (base_pool['above_50ema'] == 1)
        ].copy()
        picks['horizon_label'] = "💎 Long-Term Compounder (6-12 Months)"
        picks['target_1_pct'] = 35.0
        picks['target_2_pct'] = 60.0
        picks['stop_loss_pct'] = -12.0
        picks['setup_type'] = "Core Compounder / Structural Bull"
        picks['sort_key'] = picks['stock_strength_score']

    if picks.empty:
        return pd.DataFrame()

    # Calculate Price Targets & Stop Losses
    picks['entry_price'] = picks['close_price']
    picks['target_1_price'] = picks['entry_price'] * (1.0 + (picks['target_1_pct'] / 100.0))
    picks['target_2_price'] = picks['entry_price'] * (1.0 + (picks['target_2_pct'] / 100.0))
    picks['stop_loss_price'] = picks['entry_price'] * (1.0 + (picks['stop_loss_pct'] / 100.0))
    
    # Sort and take top 8 quality setups max (Zero spam)
    picks = picks.sort_values(by='sort_key', ascending=False).head(8).reset_index(drop=True)
    picks['rank'] = np.arange(1, len(picks) + 1)
    
    return picks


def compute_trade_lifecycle_ledger(db: Database, current_date: str) -> pd.DataFrame:
    """
    Tracks all historical quality picks from prior sessions to current_date.
    Evaluates whether each trade hit Target 1, Target 2, Stop Loss, or remains Active.
    """
    dates = db.get_existing_price_dates()
    if len(dates) < 5:
        return pd.DataFrame()
    
    recent_dates = [d for d in dates if d <= current_date][-15:]
    if len(recent_dates) < 2:
        return pd.DataFrame()
    
    conn = db.get_connection()
    all_trades = []
    
    start_d = recent_dates[0]
    df_prices = pd.read_sql("""
        SELECT symbol, date, close
        FROM stock_metrics
        WHERE date >= ? AND date <= ?
        ORDER BY symbol, date
    """, conn, params=[start_d, current_date])
    
    if df_prices.empty:
        return pd.DataFrame()

    price_dict = {}
    for sym, group in df_prices.groupby('symbol'):
        price_dict[sym] = group.set_index('date')['close'].to_dict()

    for d in recent_dates[:-1]:
        try:
            d_picks = compute_quality_picks_for_session(d, horizon="DAILY")
            w_picks = compute_quality_picks_for_session(d, horizon="WEEKLY")
            session_picks = pd.concat([d_picks.head(3), w_picks.head(3)], ignore_index=True) if not d_picks.empty or not w_picks.empty else pd.DataFrame()
        except Exception:
            session_picks = pd.DataFrame()
            
        if session_picks.empty:
            continue
            
        for _, p in session_picks.iterrows():
            sym = p['symbol']
            entry_p = p['entry_price']
            t1_p = p['target_1_price']
            t2_p = p['target_2_price']
            sl_p = p['stop_loss_price']
            
            sub_dates = [sd for sd in recent_dates if sd > d]
            if not sub_dates:
                continue
                
            sym_prices = price_dict.get(sym, {})
            realized_status = "🟢 ACTIVE"
            exit_price = entry_p
            exit_date = current_date
            max_gain_pct = 0.0
            min_loss_pct = 0.0
            
            for sd in sub_dates:
                curr_p = sym_prices.get(sd, None)
                if curr_p is None:
                    continue
                exit_price = curr_p
                exit_date = sd
                
                pnl = ((curr_p - entry_p) / entry_p) * 100.0
                if pnl > max_gain_pct:
                    max_gain_pct = pnl
                if pnl < min_loss_pct:
                    min_loss_pct = pnl
                
                if curr_p >= t2_p:
                    realized_status = "🏆 TARGET 2 HIT"
                    break
                elif curr_p >= t1_p:
                    realized_status = "🎯 TARGET 1 HIT"
                elif curr_p <= sl_p:
                    realized_status = "🛑 STOP LOSS HIT"
                    break

            latest_curr_p = sym_prices.get(current_date, exit_price)
            current_pnl_pct = ((latest_curr_p - entry_p) / entry_p) * 100.0
            
            all_trades.append({
                "entry_date": d,
                "symbol": sym,
                "company_name": p.get("company_name", sym),
                "industry": p.get("industry", ""),
                "horizon": "DAILY" if "Daily" in p.get("horizon_label", "") else "WEEKLY",
                "setup_type": p.get("setup_type", "Momentum"),
                "entry_price": entry_p,
                "target_1_price": t1_p,
                "stop_loss_price": sl_p,
                "current_price": latest_curr_p,
                "current_pnl_pct": current_pnl_pct,
                "max_gain_pct": max_gain_pct,
                "status": realized_status,
                "last_active_date": exit_date
            })

    if not all_trades:
        return pd.DataFrame()
        
    df_ledger = pd.DataFrame(all_trades)
    return df_ledger.sort_values(by='entry_date', ascending=False).reset_index(drop=True)


def render_quality_picks_dashboard(db: Database, selected_date: str):
    """
    Renders the institutional High-Conviction Quality Picks & Lifecycle Tracker UI.
    """
    t = get_theme_tokens()
    
    st.markdown(f"""
    <div style="background-color: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 14px 20px; margin-bottom: 16px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
    <div>
    <div style="font-size: 0.70rem; font-weight: 700; color: {t['text_dim']}; text-transform: uppercase; letter-spacing: 0.06em;">INSTITUTIONAL QUALITY CRITERIA</div>
    <div style="font-size: 1.25rem; font-weight: 800; color: {t['text_primary']}; margin-top: 2px;">
    🎯 Multi-Horizon High-Conviction Picks & Trade Lifecycle Ledger
    </div>
    </div>
    <div style="background: {t['secondary_bg']}; border: 1px solid {t['card_border']}; padding: 6px 12px; border-radius: 6px; font-size: 0.76rem; color: {t['text_muted']};">
    🛡️ <b>Zero-Compulsion Principle:</b> Only trades with volume surges, pattern breakouts, and top-decile quant momentum are selected.
    </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚡ Daily Momentum (1-3D)",
        "📅 Weekly Swing (1-2W)",
        "🗓️ Monthly Position (1-3M)",
        "💎 Long-Term Compounders (6-12M)",
        "📊 Trade Lifecycle & Accuracy Ledger"
    ])

    with tab1:
        render_horizon_picks_view(selected_date, horizon="DAILY", t=t)

    with tab2:
        render_horizon_picks_view(selected_date, horizon="WEEKLY", t=t)

    with tab3:
        render_horizon_picks_view(selected_date, horizon="MONTHLY", t=t)

    with tab4:
        render_horizon_picks_view(selected_date, horizon="LONG_TERM", t=t)

    with tab5:
        render_trade_ledger_view(db, selected_date, t=t)


def render_horizon_picks_view(selected_date: str, horizon: str, t: Dict[str, str]):
    picks_df = compute_quality_picks_for_session(selected_date, horizon=horizon)
    
    if picks_df.empty:
        st.info(f"🛡️ **No High-Conviction {horizon} Setups Today.** (Quality Filter is Active to Preserve Capital — Market is in Defensive Mode).")
        return

    st.markdown(f"<div style='font-size: 0.85rem; color: {t['text_muted']}; margin-bottom: 12px;'>Displaying <b>{len(picks_df)}</b> high-conviction institutional setups for session <b>{selected_date}</b>:</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    cols = [col1, col2]
    
    for idx, r in picks_df.iterrows():
        target_col = cols[idx % 2]
        with target_col:
            st_color = t["positive"] if r['stock_strength_score'] >= 75 else t["accent"]
            card_html = f"""
            <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; transition: all 0.15s ease-in-out;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 8px;">
            <div>
            <div style="display: flex; align-items: center; gap: 8px;">
            <span style="background: {t['accent_muted']}; color: {t['accent']}; border: 1px solid {t['accent']}; padding: 1px 6px; border-radius: 4px; font-weight: 800; font-size: 0.70rem; font-family: 'JetBrains Mono';">#{r['rank']:02d}</span>
            <span style="font-size: 1.05rem; font-weight: 800; color: {t['text_primary']}; font-family: 'JetBrains Mono';">{r['symbol']}</span>
            </div>
            <div style="font-size: 0.72rem; color: {t['text_muted']}; margin-top: 2px;">{r['company_name'][:28]} · <b style="color: {t['text_secondary']};">{r['industry']}</b></div>
            </div>
            <div style="text-align: right;">
            <span style="background: {t['positive_bg']}; color: {t['positive']}; border: 1px solid {t['positive_border']}; padding: 2px 8px; border-radius: 4px; font-size: 0.68rem; font-weight: 800; font-family: 'JetBrains Mono';">🟢 {r['final_action']}</span>
            <div style="font-size: 0.65rem; color: {t['text_dim']}; margin-top: 3px; font-weight: 600;">{r['setup_type']}</div>
            </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; background: {t['secondary_bg']}; padding: 8px 10px; border-radius: 6px; border: 1px solid {t['card_border']}; margin-bottom: 10px;">
            <div class="card-metric-col">
            <div class="card-metric-label">ENTRY PRICE</div>
            <div class="card-metric-value">₹{r['entry_price']:.2f}</div>
            </div>
            <div class="card-metric-col">
            <div class="card-metric-label">TARGET 1 (+{r['target_1_pct']}%)</div>
            <div class="card-metric-value" style="color: {t['positive']};">₹{r['target_1_price']:.2f}</div>
            </div>
            <div class="card-metric-col">
            <div class="card-metric-label">TARGET 2 (+{r['target_2_pct']}%)</div>
            <div class="card-metric-value" style="color: {t['positive']};">₹{r['target_2_price']:.2f}</div>
            </div>
            <div class="card-metric-col">
            <div class="card-metric-label">STOP LOSS ({r['stop_loss_pct']}%)</div>
            <div class="card-metric-value" style="color: {t['negative']};">₹{r['stop_loss_price']:.2f}</div>
            </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.70rem; color: {t['text_muted']}; font-family: 'JetBrains Mono';">
            <div>QUANT SCORE: <b style="color: {st_color};">{r['stock_strength_score']:.1f}/100</b></div>
            <div>VOL RATIO: <b style="color: {t['text_primary']};">{r['volume_ratio']:.2f}x</b></div>
            <div>RS 20D: <b style="color: {t['positive'] if r['rs_20d'] > 0 else t['negative']};">{r['rs_20d']:+.1f}%</b></div>
            </div>
            </div>
            """
            st.markdown(textwrap.dedent(card_html).strip(), unsafe_allow_html=True)


def render_trade_ledger_view(db: Database, selected_date: str, t: Dict[str, str]):
    df_ledger = compute_trade_lifecycle_ledger(db, selected_date)
    
    if df_ledger.empty:
        st.info("No historical trades in tracking window.")
        return

    # Calculate Performance Statistics
    total_trades = len(df_ledger)
    target_hits = (df_ledger['status'].isin(['🎯 TARGET 1 HIT', '🏆 TARGET 2 HIT'])).sum()
    sl_hits = (df_ledger['status'] == '🛑 STOP LOSS HIT').sum()
    active_cnt = (df_ledger['status'] == '🟢 ACTIVE').sum()
    
    closed_trades = df_ledger[df_ledger['status'] != '🟢 ACTIVE']
    win_rate = (target_hits / max(len(closed_trades), 1)) * 100.0 if not closed_trades.empty else 0.0
    avg_pnl = df_ledger['current_pnl_pct'].mean()
    
    # KPI Summary Cards
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px;">
    <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; padding: 10px 14px; border-radius: 6px;">
    <div style="font-size: 0.65rem; color: {t['text_dim']}; font-weight: 700;">TOTAL TRACKED TRADES</div>
    <div style="font-size: 1.3rem; font-weight: 800; color: {t['text_primary']}; font-family: 'JetBrains Mono';">{total_trades}</div>
    </div>
    <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; padding: 10px 14px; border-radius: 6px;">
    <div style="font-size: 0.65rem; color: {t['text_dim']}; font-weight: 700;">TARGET 1 / 2 HIT RATE</div>
    <div style="font-size: 1.3rem; font-weight: 800; color: {t['positive']}; font-family: 'JetBrains Mono';">{win_rate:.1f}% <span style="font-size: 0.70rem; color: {t['text_muted']};">({target_hits}/{len(closed_trades)})</span></div>
    </div>
    <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; padding: 10px 14px; border-radius: 6px;">
    <div style="font-size: 0.65rem; color: {t['text_dim']}; font-weight: 700;">STOP LOSS HIT</div>
    <div style="font-size: 1.3rem; font-weight: 800; color: {t['negative']}; font-family: 'JetBrains Mono';">{sl_hits}</div>
    </div>
    <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; padding: 10px 14px; border-radius: 6px;">
    <div style="font-size: 0.65rem; color: {t['text_dim']}; font-weight: 700;">AVG REALIZED P&L</div>
    <div style="font-size: 1.3rem; font-weight: 800; color: {t['positive'] if avg_pnl > 0 else t['negative']}; font-family: 'JetBrains Mono';">{avg_pnl:+.2f}%</div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Format Display Table
    disp_df = df_ledger[[
        'entry_date', 'symbol', 'company_name', 'horizon', 'setup_type',
        'entry_price', 'target_1_price', 'stop_loss_price', 'current_price',
        'current_pnl_pct', 'status'
    ]].copy()
    
    disp_df.columns = [
        'Entry Date', 'Symbol', 'Company', 'Horizon', 'Setup',
        'Entry (₹)', 'Target 1 (₹)', 'Stop Loss (₹)', 'Current (₹)',
        'P&L %', 'Status'
    ]
    
    # Render interactive dataframe
    st.dataframe(
        disp_df.style.format({
            'Entry (₹)': '₹{:.2f}',
            'Target 1 (₹)': '₹{:.2f}',
            'Stop Loss (₹)': '₹{:.2f}',
            'Current (₹)': '₹{:.2f}',
            'P&L %': '{:+.2f}%'
        }),
        use_container_width=True,
        height=380
    )
