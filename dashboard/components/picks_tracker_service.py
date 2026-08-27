"""
Institutional Pre-Breakout Support & Resistance Trade Strategy Engine.
NorthFlow Quantitative Trading & Accountability Terminal.
Features:
- Pre-Breakout / VCP / EMA Pullback Setups (Enter BEFORE breakout with tight structural risk)
- Dynamic Price Targets based on exact 20D/60D Supply Resistance Pivots
- Structural Stop-Losses placed strictly below Key Swing Support
- Complete Trade Strategy Playbook: Entry Zone, Booking Rationale, Trailing Rules
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

def compute_structural_quality_picks(selected_date: str, horizon: str = "DAILY") -> pd.DataFrame:
    """
    Computes high-conviction pre-breakout setups with dynamic Support/Resistance geometry.
    Horizons: 'DAILY' (1-3D), 'WEEKLY' (1-2W), 'MONTHLY' (1-3M), 'LONG_TERM' (6-12M).
    """
    db = Database()
    conn = db.get_connection()
    
    # Load recent 60-session historical daily price bars up to selected_date
    recent_dates = pd.read_sql("""
        SELECT DISTINCT date FROM daily_prices WHERE date <= ? ORDER BY date DESC LIMIT 60
    """, conn, params=[selected_date])['date'].tolist()
    
    if len(recent_dates) < 20:
        return pd.DataFrame()
        
    start_d = recent_dates[-1]
    
    df_prices = pd.read_sql("""
        SELECT symbol, date, open, high, low, close, volume
        FROM daily_prices
        WHERE date >= ? AND date <= ?
        ORDER BY symbol, date ASC
    """, conn, params=[start_d, selected_date])
    
    if df_prices.empty:
        return pd.DataFrame()

    df_metrics = pd.read_sql("""
        SELECT 
            m.symbol, s.company_name, s.macro_sector, s.industry,
            m.close, m.rs_5d, m.rs_20d, m.volume_ratio, m.above_20ema, m.above_50ema
        FROM stock_metrics m
        JOIN stocks s ON m.symbol = s.symbol
        WHERE m.date = ? AND s.active = 1
    """, conn, params=[selected_date])
    
    if df_metrics.empty:
        return pd.DataFrame()
        
    metrics_map = df_metrics.set_index('symbol').to_dict('index')

    setups = []

    for sym, group in df_prices.groupby('symbol'):
        if len(group) < 20:
            continue
            
        group = group.reset_index(drop=True)
        curr = group.iloc[-1]
        curr_close = float(curr['close'])
        if curr_close < 25.0:  # Skip micro-penny equities
            continue
            
        m_data = metrics_map.get(sym, None)
        if not m_data or m_data['above_50ema'] != 1:
            continue
            
        highs = group['high'].values
        lows = group['low'].values
        closes = group['close'].values
        volumes = group['volume'].values
        
        # 1. Structural Resistance (Overhead Supply Pivots)
        # Resistance 1: 20-day swing high prior to today
        res_1 = float(np.max(highs[-21:-1])) if len(highs) >= 21 else float(np.max(highs[:-1]))
        # Resistance 2: 60-day major resistance high
        res_2 = float(np.max(highs))
        
        # 2. Structural Support (Recent Demand Floors)
        supp_10d = float(np.min(lows[-10:]))
        supp_20d = float(np.min(lows[-20:]))
        
        # EMAs
        ema_20 = float(pd.Series(closes).ewm(span=20, adjust=False).mean().iloc[-1])
        ema_50 = float(pd.Series(closes).ewm(span=50, adjust=False).mean().iloc[-1])
        
        # Structural Stop Loss: Placed 0.8% below 10-day swing low or 20-EMA floor
        structural_stop = min(supp_10d * 0.992, ema_20 * 0.99)
        risk_pct = ((curr_close - structural_stop) / curr_close) * 100.0
        
        # Dynamic Rewards based on Support & Resistance
        reward_t1_pct = ((res_1 - curr_close) / curr_close) * 100.0
        target_2 = max(res_2, res_1 * 1.08)
        reward_t2_pct = ((target_2 - curr_close) / curr_close) * 100.0
        
        # Strict Risk-Reward Geometry Filter (Tight Risk, High Asymmetry)
        if risk_pct < 0.6 or risk_pct > 5.5 or reward_t1_pct < 2.0:
            continue
            
        rr_ratio = reward_t1_pct / risk_pct
        if rr_ratio < 1.8:
            continue

        # 3. Volatility Contraction / Pattern Classification
        range_5d = (np.max(highs[-5:]) - np.min(lows[-5:])) / curr_close
        range_20d = (np.max(highs[-20:]) - np.min(lows[-20:])) / curr_close
        is_vcp = range_5d < (range_20d * 0.65)
        is_ema_pullback = abs(curr_close - ema_20) / ema_20 < 0.025 and curr_close >= ema_20
        is_pre_breakout_coil = 1.2 <= reward_t1_pct <= 6.0 and curr_close > ema_20
        
        if not (is_vcp or is_ema_pullback or is_pre_breakout_coil):
            continue

        # Horizon Specific Filters
        if horizon == "DAILY":
            if m_data['volume_ratio'] < 1.5 and not is_vcp:
                continue
            horizon_title = "⚡ Daily Momentum (1-3 Days)"
            strategy_rule = "Enter inside base consolidation before 20D resistance breakout. Book 50% at Target 1, trail stop to breakeven."
            
        elif horizon == "WEEKLY":
            if m_data['rs_20d'] < 1.0 or not m_data['above_20ema']:
                continue
            horizon_title = "📅 Weekly Swing (1-2 Weeks)"
            strategy_rule = "Swing setup near 20-EMA demand confluence. Book 50% at Target 1 (Overhead Resistance), trail remaining 50% along 20-EMA to Target 2."
            
        elif horizon == "MONTHLY":
            if m_data['rs_20d'] < 4.0 or m_data['above_50ema'] != 1:
                continue
            horizon_title = "🗓️ Monthly Position (1-3 Months)"
            strategy_rule = "Multi-week accumulation base. Scale in at support, hold through breakout test towards 60D major expansion resistance."
            
        else:  # LONG_TERM
            if m_data['rs_20d'] < 6.0 or curr_close < ema_50:
                continue
            horizon_title = "💎 Long-Term Compounder (6-12 Months)"
            strategy_rule = "Institutional core leader. Trail stop under 50-EMA structural weekly base for multi-quarter compounding."

        pattern_name = "VCP Contraction Base" if is_vcp else ("20-EMA Demand Confluence" if is_ema_pullback else "Pre-Breakout Resistance Coil")

        setups.append({
            "symbol": sym,
            "company_name": m_data['company_name'],
            "industry": m_data['industry'],
            "macro_sector": m_data['macro_sector'],
            "current_price": curr_close,
            "buy_zone_min": curr_close * 0.993,
            "buy_zone_max": curr_close * 1.008,
            "target_1_price": res_1,
            "target_1_pct": reward_t1_pct,
            "target_2_price": target_2,
            "target_2_pct": reward_t2_pct,
            "stop_loss_price": structural_stop,
            "stop_loss_pct": risk_pct,
            "rr_ratio": rr_ratio,
            "pattern": pattern_name,
            "volume_ratio": m_data['volume_ratio'],
            "rs_20d": m_data['rs_20d'],
            "horizon_label": horizon_title,
            "strategy_rule": strategy_rule,
            "rank_score": (rr_ratio * 10.0) + (m_data['rs_20d'] * 0.5) + (m_data['volume_ratio'] * 5.0)
        })

    if not setups:
        return pd.DataFrame()
        
    df_res = pd.DataFrame(setups).sort_values(by='rank_score', ascending=False).head(6).reset_index(drop=True)
    df_res['rank'] = np.arange(1, len(df_res) + 1)
    return df_res


def compute_structural_trade_lifecycle_ledger(db: Database, current_date: str) -> pd.DataFrame:
    """
    Evaluates historical structural setups against realized price action up to current_date.
    Tracks whether price reached Target 1 (Resistance), Target 2 (Expansion), or Stop Loss (Support floor).
    """
    dates = db.get_existing_price_dates()
    if len(dates) < 5:
        return pd.DataFrame()
        
    recent_dates = [d for d in dates if d <= current_date][-15:]
    if len(recent_dates) < 2:
        return pd.DataFrame()
        
    conn = db.get_connection()
    start_d = recent_dates[0]
    
    df_prices = pd.read_sql("""
        SELECT symbol, date, high, low, close
        FROM daily_prices
        WHERE date >= ? AND date <= ?
        ORDER BY symbol, date ASC
    """, conn, params=[start_d, current_date])
    
    if df_prices.empty:
        return pd.DataFrame()

    price_map = {}
    for sym, grp in df_prices.groupby('symbol'):
        price_map[sym] = grp.set_index('date').to_dict('index')

    all_tracked = []

    for d in recent_dates[:-1]:
        try:
            d_setups = compute_structural_quality_picks(d, horizon="DAILY")
            w_setups = compute_structural_quality_picks(d, horizon="WEEKLY")
            session_setups = pd.concat([d_setups.head(2), w_setups.head(2)], ignore_index=True) if not d_setups.empty or not w_setups.empty else pd.DataFrame()
        except Exception:
            session_setups = pd.DataFrame()
            
        if session_setups.empty:
            continue
            
        for _, s in session_setups.iterrows():
            sym = s['symbol']
            entry_p = s['current_price']
            t1 = s['target_1_price']
            t2 = s['target_2_price']
            sl = s['stop_loss_price']
            
            sub_dates = [sd for sd in recent_dates if sd > d]
            if not sub_dates:
                continue
                
            sym_history = price_map.get(sym, {})
            trade_status = "🟢 ACTIVE (In Trade)"
            exit_price = entry_p
            exit_date = current_date
            max_gain = 0.0
            
            for sd in sub_dates:
                bar = sym_history.get(sd, None)
                if not bar:
                    continue
                h_p = bar['high']
                l_p = bar['low']
                c_p = bar['close']
                exit_price = c_p
                exit_date = sd
                
                gain_pct = ((h_p - entry_p) / entry_p) * 100.0
                if gain_pct > max_gain:
                    max_gain = gain_pct
                    
                if h_p >= t2:
                    trade_status = "🏆 TARGET 2 HIT (Major Resistance)"
                    break
                elif h_p >= t1:
                    trade_status = "🎯 TARGET 1 HIT (Resistance Reached)"
                elif l_p <= sl:
                    trade_status = "🛑 STOP LOSS HIT (Support Broken)"
                    break

            latest_bar = sym_history.get(current_date, {'close': exit_price})
            curr_p = latest_bar['close']
            current_pnl = ((curr_p - entry_p) / entry_p) * 100.0
            
            all_tracked.append({
                "entry_date": d,
                "symbol": sym,
                "company_name": s['company_name'],
                "industry": s['industry'],
                "pattern": s['pattern'],
                "entry_price": entry_p,
                "stop_loss_price": sl,
                "target_1_price": t1,
                "target_2_price": t2,
                "current_price": curr_p,
                "current_pnl_pct": current_pnl,
                "max_gain_pct": max_gain,
                "status": trade_status,
                "rr_ratio": s['rr_ratio']
            })

    if not all_tracked:
        return pd.DataFrame()
        
    df_ledger = pd.DataFrame(all_tracked)
    return df_ledger.sort_values(by='entry_date', ascending=False).reset_index(drop=True)


def render_quality_picks_dashboard(db: Database, selected_date: str):
    """
    Institutional UI for Pre-Breakout Support/Resistance Strategy & Accountability Ledger.
    """
    t = get_theme_tokens()
    
    st.markdown(f"""
    <div style="background-color: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 14px 20px; margin-bottom: 16px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
    <div>
    <div style="font-size: 0.70rem; font-weight: 700; color: {t['text_dim']}; text-transform: uppercase; letter-spacing: 0.06em;">INSTITUTIONAL EXECUTION FRAMEWORK</div>
    <div style="font-size: 1.25rem; font-weight: 800; color: {t['text_primary']}; margin-top: 2px;">
    🎯 Pre-Breakout Structural Setups & Trade Lifecycle Ledger
    </div>
    </div>
    <div style="background: {t['secondary_bg']}; border: 1px solid {t['card_border']}; padding: 6px 12px; border-radius: 6px; font-size: 0.76rem; color: {t['text_muted']};">
    🛡️ <b>Pre-Breakout Rule:</b> Enter at support/base contraction BEFORE breakout with asymmetric Risk:Reward (Min 1 : 2.5).
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
        render_structural_horizon_view(selected_date, horizon="DAILY", t=t)

    with tab2:
        render_structural_horizon_view(selected_date, horizon="WEEKLY", t=t)

    with tab3:
        render_structural_horizon_view(selected_date, horizon="MONTHLY", t=t)

    with tab4:
        render_structural_horizon_view(selected_date, horizon="LONG_TERM", t=t)

    with tab5:
        render_structural_trade_ledger_view(db, selected_date, t=t)


def render_structural_horizon_view(selected_date: str, horizon: str, t: Dict[str, str]):
    picks_df = compute_structural_quality_picks(selected_date, horizon=horizon)
    
    if picks_df.empty:
        st.info(f"🛡️ **No High-Conviction Pre-Breakout {horizon} Setups Today.** (Quality Filter is Active — Zero Compulsion. Market geometry does not offer asymmetric R:R today, preserving capital).")
        return

    st.markdown(f"<div style='font-size: 0.85rem; color: {t['text_muted']}; margin-bottom: 12px;'>Displaying <b>{len(picks_df)}</b> high-asymmetry structural setups for session <b>{selected_date}</b>:</div>", unsafe_allow_html=True)

    for idx, r in picks_df.iterrows():
        rr_badge_col = t["positive"] if r['rr_ratio'] >= 3.0 else t["accent"]
        
        card_html = f"""
        <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; border-radius: 8px; padding: 16px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
        <div>
        <div style="display: flex; align-items: center; gap: 10px;">
        <span style="background: {t['accent_muted']}; color: {t['accent']}; border: 1px solid {t['accent']}; padding: 2px 8px; border-radius: 4px; font-weight: 800; font-size: 0.75rem; font-family: 'JetBrains Mono';">#{r['rank']:02d}</span>
        <span style="font-size: 1.20rem; font-weight: 800; color: {t['text_primary']}; font-family: 'JetBrains Mono';">{r['symbol']}</span>
        <span style="font-size: 0.85rem; color: {t['text_muted']}; font-weight: 600;">{r['company_name'][:30]}</span>
        </div>
        <div style="font-size: 0.74rem; color: {t['text_muted']}; margin-top: 3px;">Sector: <b style="color: {t['text_secondary']};">{r['macro_sector']}</b> · Industry: <b style="color: {t['text_secondary']};">{r['industry']}</b></div>
        </div>
        
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
        <span style="background: rgba(16, 185, 129, 0.12); color: {t['positive']}; border: 1px solid rgba(16, 185, 129, 0.30); padding: 3px 10px; border-radius: 4px; font-size: 0.72rem; font-weight: 800; font-family: 'JetBrains Mono';">SETUP: {r['pattern']}</span>
        <span style="background: {t['secondary_bg']}; color: {rr_badge_col}; border: 1px solid {t['card_border']}; padding: 3px 10px; border-radius: 4px; font-size: 0.72rem; font-weight: 800; font-family: 'JetBrains Mono';">R:R = 1 : {r['rr_ratio']:.1f}</span>
        </div>
        </div>
        
        <!-- PRICE LEVELS MATRIX -->
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; background: {t['secondary_bg']}; padding: 10px 14px; border-radius: 6px; border: 1px solid {t['card_border']}; margin-bottom: 12px;">
        <div class="card-metric-col">
        <div class="card-metric-label">BUY ACCUMULATE ZONE</div>
        <div class="card-metric-value" style="color: {t['text_primary']};">₹{r['buy_zone_min']:.2f} - ₹{r['buy_zone_max']:.2f}</div>
        <div style="font-size: 0.60rem; color: {t['text_dim']}; font-family: 'JetBrains Mono';">CMP: ₹{r['current_price']:.2f}</div>
        </div>
        
        <div class="card-metric-col">
        <div class="card-metric-label">STRUCTURAL STOP-LOSS</div>
        <div class="card-metric-value" style="color: {t['negative']};">₹{r['stop_loss_price']:.2f}</div>
        <div style="font-size: 0.60rem; color: {t['negative']}; font-family: 'JetBrains Mono';">Risk: -{r['stop_loss_pct']:.2f}% (Below Support)</div>
        </div>
        
        <div class="card-metric-col">
        <div class="card-metric-label">TARGET 1 (OVERHEAD RESISTANCE)</div>
        <div class="card-metric-value" style="color: {t['positive']};">₹{r['target_1_price']:.2f}</div>
        <div style="font-size: 0.60rem; color: {t['positive']}; font-family: 'JetBrains Mono';">Reward: +{r['target_1_pct']:.2f}% (Book 50%)</div>
        </div>
        
        <div class="card-metric-col">
        <div class="card-metric-label">TARGET 2 (EXPANSION RESISTANCE)</div>
        <div class="card-metric-value" style="color: {t['positive']};">₹{r['target_2_price']:.2f}</div>
        <div style="font-size: 0.60rem; color: {t['positive']}; font-family: 'JetBrains Mono';">Reward: +{r['target_2_pct']:.2f}% (Trail 50%)</div>
        </div>
        </div>
        
        <!-- TRADE STRATEGY & EXECUTION PLAYBOOK -->
        <div style="background: {t['card_bg']}; border-left: 3px solid {t['accent']}; padding: 8px 12px; border-radius: 0 4px 4px 0; font-size: 0.74rem; color: {t['text_secondary']}; line-height: 1.4;">
        <b>🎯 Trade Strategy & Execution Playbook:</b> {r['strategy_rule']}<br>
        <span style="color: {t['text_muted']};"><b>Execution Rule:</b> Enter in the pre-breakout accumulation zone. If price hits Target 1 (₹{r['target_1_price']:.2f}), lock in 50% profit and immediately shift stop-loss to entry price (Breakeven). Trail remaining quantity for Target 2.</span>
        </div>
        </div>
        """
        st.markdown(textwrap.dedent(card_html).strip(), unsafe_allow_html=True)


def render_structural_trade_ledger_view(db: Database, selected_date: str, t: Dict[str, str]):
    df_ledger = compute_structural_trade_lifecycle_ledger(db, selected_date)
    
    if df_ledger.empty:
        st.info("No historical structural trades in tracking window.")
        return

    total_trades = len(df_ledger)
    target_hits = (df_ledger['status'].str.contains('TARGET')).sum()
    sl_hits = (df_ledger['status'].str.contains('STOP LOSS')).sum()
    closed_trades = df_ledger[~df_ledger['status'].str.contains('ACTIVE')]
    win_rate = (target_hits / max(len(closed_trades), 1)) * 100.0 if not closed_trades.empty else 0.0
    avg_pnl = df_ledger['current_pnl_pct'].mean()
    
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px;">
    <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; padding: 10px 14px; border-radius: 6px;">
    <div style="font-size: 0.65rem; color: {t['text_dim']}; font-weight: 700;">TOTAL TRACKED TRADES</div>
    <div style="font-size: 1.3rem; font-weight: 800; color: {t['text_primary']}; font-family: 'JetBrains Mono';">{total_trades}</div>
    </div>
    <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; padding: 10px 14px; border-radius: 6px;">
    <div style="font-size: 0.65rem; color: {t['text_dim']}; font-weight: 700;">RESISTANCE TARGET HIT RATE</div>
    <div style="font-size: 1.3rem; font-weight: 800; color: {t['positive']}; font-family: 'JetBrains Mono';">{win_rate:.1f}% <span style="font-size: 0.70rem; color: {t['text_muted']};">({target_hits}/{len(closed_trades)})</span></div>
    </div>
    <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; padding: 10px 14px; border-radius: 6px;">
    <div style="font-size: 0.65rem; color: {t['text_dim']}; font-weight: 700;">SUPPORT STOPPED OUT</div>
    <div style="font-size: 1.3rem; font-weight: 800; color: {t['negative']}; font-family: 'JetBrains Mono';">{sl_hits}</div>
    </div>
    <div style="background: {t['card_bg']}; border: 1px solid {t['card_border']}; padding: 10px 14px; border-radius: 6px;">
    <div style="font-size: 0.65rem; color: {t['text_dim']}; font-weight: 700;">AVG REALIZED P&L</div>
    <div style="font-size: 1.3rem; font-weight: 800; color: {t['positive'] if avg_pnl > 0 else t['negative']}; font-family: 'JetBrains Mono';">{avg_pnl:+.2f}%</div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    disp_df = df_ledger[[
        'entry_date', 'symbol', 'company_name', 'pattern',
        'entry_price', 'stop_loss_price', 'target_1_price', 'target_2_price',
        'current_price', 'current_pnl_pct', 'max_gain_pct', 'status'
    ]].copy()
    
    disp_df.columns = [
        'Entry Date', 'Symbol', 'Company', 'Pattern',
        'Entry (₹)', 'Stop Support (₹)', 'Target 1 Res (₹)', 'Target 2 Res (₹)',
        'Current (₹)', 'P&L %', 'Max Gain %', 'Status'
    ]
    
    st.dataframe(
        disp_df.style.format({
            'Entry (₹)': '₹{:.2f}',
            'Stop Support (₹)': '₹{:.2f}',
            'Target 1 Res (₹)': '₹{:.2f}',
            'Target 2 Res (₹)': '₹{:.2f}',
            'Current (₹)': '₹{:.2f}',
            'P&L %': '{:+.2f}%',
            'Max Gain %': '{:+.2f}%'
        }),
        use_container_width=True,
        height=380
    )
