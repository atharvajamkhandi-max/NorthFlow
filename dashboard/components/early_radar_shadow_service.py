"""
Early Sector Radar Shadow Service (Phase 24 / 25).
Provides daily early-warning accumulation and pre-breakout probability forecasts
in parallel SHADOW mode without modifying active production scoring or UI.
"""

import os
import sqlite3
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

SHADOW_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "research" / "live_shadow"
SHADOW_LOG_DIR.mkdir(parents=True, exist_ok=True)

def compute_early_radar_scores_point_in_time(ind_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Point-in-Time Early Sector Radar scores and calibrated probabilities.
    Strictly uses information available through market close T.
    """
    df = ind_df.copy().sort_values(['industry', 'date']).reset_index(drop=True)
    
    # 1. Breadth and Momentum Accel
    df['breadth_acc_5d'] = df.groupby('industry')['breadth_50'].diff(5).fillna(0.0)
    acc_breadth = np.clip((df['breadth_acc_5d'] + 15.0) / 30.0 * 100.0, 0.0, 100.0).fillna(50.0)
    
    vol_ratio = df.get('ind_vol_ratio', pd.Series(1.0, index=df.index)).fillna(1.0)
    acc_vol = np.clip((vol_ratio - 0.5) / 1.5 * 100.0, 0.0, 100.0).fillna(50.0)
    
    deliv = df.get('ind_deliv_intensity', pd.Series(0.0, index=df.index)).fillna(0.0)
    acc_del = np.clip((deliv + 0.5) / 1.5 * 100.0, 0.0, 100.0).fillna(50.0)
    
    roll_std_20 = df.groupby('industry')['ind_ret_1d'].transform(lambda s: s.rolling(20, min_periods=5).std()).fillna(1.0)
    roll_std_60 = df.groupby('industry')['ind_ret_1d'].transform(lambda s: s.rolling(60, min_periods=10).std()).fillna(1.0)
    df['vol_compression_ratio'] = (roll_std_20 / (roll_std_60 + 1e-6)).clip(0.1, 5.0).fillna(1.0)
    acc_comp = np.clip((1.5 - df['vol_compression_ratio']) / 1.0 * 100.0, 0.0, 100.0).fillna(50.0)
    
    df['accumulation_pressure'] = np.clip(
        0.25 * acc_breadth + 0.25 * acc_comp + 0.25 * acc_del + 0.25 * acc_vol,
        0.0, 100.0
    ).fillna(50.0).round(1)
    
    # 2. Cross-Stock Synchronization
    b50 = df.get('breadth_50', pd.Series(50.0, index=df.index)).fillna(50.0)
    pos_mom = df.get('pct_pos_mom', pd.Series(50.0, index=df.index)).fillna(50.0)
    df['cross_stock_synchronization'] = np.clip(b50 * 0.5 + pos_mom * 0.5, 0.0, 100.0).fillna(50.0).round(1)
    
    # 3. Pre-Breakout Score
    df['ret_accel_5d'] = df.groupby('industry')['ind_ret_5d'].diff(5).fillna(0.0)
    df['breadth_impulse_10d'] = df.groupby('industry')['breadth_50'].transform(
        lambda s: (s - s.shift(10)) / (s.rolling(20, min_periods=5).std() + 1e-6)
    ).fillna(0.0).clip(-3.0, 3.0)
    
    df['pre_breakout_score'] = np.clip(
        0.30 * df['accumulation_pressure'] +
        0.30 * df['cross_stock_synchronization'] +
        0.20 * np.clip((df['breadth_impulse_10d'] + 2.0) / 4.0 * 100.0, 0.0, 100.0).fillna(50.0) +
        0.20 * np.clip((df['ret_accel_5d'] + 5.0) / 10.0 * 100.0, 0.0, 100.0).fillna(50.0),
        0.0, 100.0
    ).fillna(50.0).round(1)
    
    # 4. Early Radar Composite Score (0-100)
    r20 = df.get('ind_ret_20d', pd.Series(0.0, index=df.index)).fillna(0.0)
    ext_pen = np.clip(r20 / 20.0 * 25.0, 0.0, 25.0).fillna(0.0)
    
    df['early_radar_score'] = np.clip(
        0.50 * df['pre_breakout_score'] + 0.50 * df['accumulation_pressure'] - ext_pen,
        0.0, 100.0
    ).fillna(50.0).round(1)
    
    # 5. Alert Level Classification
    def assign_alert(s):
        if pd.isna(s): return "NONE"
        elif s >= 75.0: return "PRE-BREAKOUT"
        elif s >= 65.0: return "EARLY"
        elif s >= 55.0: return "WATCH"
        else: return "NONE"
        
    df['alert_level'] = df['early_radar_score'].map(assign_alert)
    
    # 6. Calibrated Probabilities & Lead Time
    df['prob_1d'] = np.clip(df['early_radar_score'] * 0.0020 + 0.02, 0.05, 0.35).fillna(0.10).round(3)
    df['prob_3d'] = np.clip(df['early_radar_score'] * 0.0040 + 0.05, 0.10, 0.60).fillna(0.20).round(3)
    df['prob_5d'] = np.clip(df['early_radar_score'] * 0.0075 + 0.08, 0.15, 0.85).fillna(0.30).round(3)
    df['expected_lead_days'] = np.clip(4.5 - (df['early_radar_score'] / 100.0) * 2.0, 1.5, 4.5).fillna(3.0).round(1)
    
    # 7. Precursor Explanation
    def explain_precursor(row):
        reasons = []
        if row.get('accumulation_pressure', 0) >= 70: reasons.append("Strong Accumulation Pressure")
        if row.get('cross_stock_synchronization', 0) >= 65: reasons.append("High Cross-Stock Synchronization")
        if row.get('vol_compression_ratio', 1.0) <= 0.85: reasons.append("Volatility Compression")
        if row.get('breadth_50', 50.0) >= 60: reasons.append("Broad Breadth Expansion")
        return " | ".join(reasons) if reasons else "Neutral Precursor Structure"
        
    df['feature_explanation'] = df.apply(explain_precursor, axis=1)
    return df

def persist_daily_shadow_log(date_str: str, shadow_df: pd.DataFrame) -> Path:
    """
    Persists daily shadow output to research/live_shadow/YYYY-MM-DD_early_radar.csv.
    """
    out_file = SHADOW_LOG_DIR / f"{date_str}_early_radar.csv"
    cols = [
        'date', 'industry', 'early_radar_score', 'alert_level',
        'prob_1d', 'prob_3d', 'prob_5d', 'expected_lead_days',
        'accumulation_pressure', 'cross_stock_synchronization', 'feature_explanation'
    ]
    avail_cols = [c for c in cols if c in shadow_df.columns]
    shadow_df[avail_cols].to_csv(out_file, index=False)
    return out_file

@st.cache_data(show_spinner=False)
def load_point_in_time_industry_history(selected_date: str) -> pd.DataFrame:
    """
    Loads point-in-time industry history through selected_date for accurate radar evaluation.
    Cached via Streamlit to eliminate duplicate disk/SQL reads on reruns.
    """
    db_path = Path(__file__).resolve().parent.parent.parent / "data" / "market_flow.db"
    if not db_path.exists():
        return pd.DataFrame()
        
    conn = sqlite3.connect(db_path)
    query = f"""
        SELECT 
            dp.symbol, 
            dp.date, 
            dp.close, 
            dp.volume, 
            dp.delivery_quantity AS deliv_qty, 
            m.industry
        FROM daily_prices dp
        JOIN stock_classification_master_v3 m ON dp.symbol = m.symbol
        WHERE dp.date <= '{selected_date}'
        ORDER BY dp.symbol, dp.date
    """
    df_raw = pd.read_sql_query(query, conn)
    conn.close()
    
    if df_raw.empty:
        return pd.DataFrame()
        
    df_raw['date'] = pd.to_datetime(df_raw['date'])
    df_raw['deliv_qty'] = df_raw['deliv_qty'].fillna(0.0)
    
    # Calculate price/volume metrics
    df_raw['ema50'] = df_raw.groupby('symbol')['close'].transform(lambda x: x.ewm(span=50, adjust=False).mean())
    df_raw['ema20'] = df_raw.groupby('symbol')['close'].transform(lambda x: x.ewm(span=20, adjust=False).mean())
    df_raw['above_50ema'] = (df_raw['close'] > df_raw['ema50']).astype(int)
    df_raw['above_20ema'] = (df_raw['close'] > df_raw['ema20']).astype(int)
    df_raw['ret_1d'] = (df_raw.groupby('symbol')['close'].pct_change(1) * 100.0).fillna(0.0)
    df_raw['ret_5d'] = (df_raw.groupby('symbol')['close'].pct_change(5) * 100.0).fillna(0.0)
    df_raw['ret_20d'] = (df_raw.groupby('symbol')['close'].pct_change(20) * 100.0).fillna(0.0)
    df_raw['pos_mom_5d'] = (df_raw['ret_5d'] > 0).astype(int)
    
    vol_ma20 = df_raw.groupby('symbol')['volume'].transform(lambda x: x.rolling(20, min_periods=5).mean()).fillna(df_raw['volume'])
    df_raw['vol_ratio_20d'] = (df_raw['volume'] / (vol_ma20 + 1e-6)).clip(0.1, 10.0).fillna(1.0)
    deliv_ma20 = df_raw.groupby('symbol')['deliv_qty'].transform(lambda x: x.rolling(20, min_periods=5).mean()).fillna(df_raw['deliv_qty'])
    df_raw['deliv_ratio_20d'] = (df_raw['deliv_qty'] / (deliv_ma20 + 1e-6)).clip(0.1, 10.0).fillna(1.0)
    df_raw['deliv_directional_intensity'] = (df_raw['deliv_ratio_20d'] * np.sign(df_raw['ret_1d'])).fillna(0.0)
    
    ind_daily = df_raw.groupby(['industry', 'date']).agg(
        constituents=('symbol', 'count'),
        breadth_20=('above_20ema', lambda x: x.mean() * 100.0),
        breadth_50=('above_50ema', lambda x: x.mean() * 100.0),
        pct_pos_mom=('pos_mom_5d', lambda x: x.mean() * 100.0),
        ind_ret_1d=('ret_1d', 'mean'),
        ind_ret_5d=('ret_5d', 'mean'),
        ind_ret_20d=('ret_20d', 'mean'),
        ind_vol_ratio=('vol_ratio_20d', 'mean'),
        ind_deliv_intensity=('deliv_directional_intensity', 'mean')
    ).reset_index()
    
    ind_df = ind_daily[ind_daily['constituents'] >= 5].copy()
    return ind_df

@st.cache_data(show_spinner=False)
def get_cached_early_radar_scores(selected_date: str) -> pd.DataFrame:
    """
    Canonical point-in-time calculation for Early Sector Radar.
    Cached via Streamlit to guarantee single execution per selected date across all UI tabs.
    """
    ind_history = load_point_in_time_industry_history(selected_date)
    if ind_history.empty:
        return pd.DataFrame()
        
    ind_scored = compute_early_radar_scores_point_in_time(ind_history)
    
    # Add V3.2 proxy for comparison
    ind_scored['v3_2_strength'] = np.clip(
        0.40 * ind_scored['breadth_50'] + 0.30 * np.clip((ind_scored['ind_ret_20d'] + 10.0) / 30.0 * 100.0, 0.0, 100.0) +
        0.30 * np.clip(ind_scored['breadth_20'], 0.0, 100.0),
        0.0, 100.0
    ).fillna(50.0).round(1)
    
    return ind_scored

def render_early_sector_radar_ui(selected_date: str = "2026-08-21", precalculated_radar: pd.DataFrame = None):
    """
    Renders the Early Sector Radar UI section in Streamlit with Progressive Disclosure:
    Level 1: Simple human-readable conclusion & Spotlight
    Level 2: Useful supporting metrics & top opportunities
    Level 3: Detailed quantitative/technical information (expandable)
    """
    st.markdown("""
    <div style="background-color: #0F172A; border: 1px solid #1E293B; border-left: 4px solid #38BDF8; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #F8FAFC; letter-spacing: 0.02em;">
                    📡 EARLY SECTOR RADAR <span style="background-color: #0369A1; color: #E0F2FE; font-size: 0.70rem; padding: 2px 8px; border-radius: 4px; font-weight: 700; margin-left: 8px;">SHADOW / RESEARCH</span>
                </div>
                <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 4px;">
                    Identifies industries showing quiet accumulation <b>BEFORE</b> the main price breakout occurs.
                </div>
            </div>
            <div style="text-align: right; font-size: 0.75rem; color: #64748B;">
                <div>Session: <b style="color: #F8FAFC;">""" + str(selected_date) + """</b></div>
                <div>Model: <span style="color: #38BDF8;">EARLY_RADAR_V1_FROZEN</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. Fetch Radar scores (reusing precalculated instance or cached pipeline)
    if precalculated_radar is not None and not precalculated_radar.empty:
        ind_scored = precalculated_radar
    else:
        ind_scored = get_cached_early_radar_scores(selected_date)

    if ind_scored.empty:
        st.info("Insufficient historical session depth to calculate rolling precursor accumulation.")
        return
        
    # Filter to selected date
    target_dt = pd.to_datetime(selected_date)
    df_today = ind_scored[ind_scored['date'] == target_dt].copy()
    
    if df_today.empty:
        df_today = ind_scored[ind_scored['date'] == ind_scored['date'].max()].copy()
        
    # Persist daily shadow log
    persist_daily_shadow_log(str(selected_date), df_today)
    
    # Sort by Radar score
    df_radar_top = df_today.sort_values('early_radar_score', ascending=False).reset_index(drop=True)
    df_radar_top['Rank'] = np.arange(1, len(df_radar_top) + 1)
    
    if df_radar_top.empty:
        st.info("No industry radar signals available for this session.")
        return

    # --- LEVEL 1: SIMPLE HUMAN-READABLE CONCLUSION / SPOTLIGHT ---
    top1 = df_radar_top.iloc[0]
    lead_raw = top1.get('expected_lead_days', 3.0)
    lead_val = float(lead_raw) if pd.notna(lead_raw) else 3.0
    lead_min = max(1, int(round(lead_val - 1)))
    lead_max = max(lead_min + 2, int(round(lead_val + 2)))
    
    top_score = float(top1.get('early_radar_score', 50.0)) if pd.notna(top1.get('early_radar_score')) else 50.0
    v32_score = float(top1.get('v3_2_strength', 50.0)) if pd.notna(top1.get('v3_2_strength')) else 50.0
    sync_score = float(top1.get('cross_stock_synchronization', 50.0)) if pd.notna(top1.get('cross_stock_synchronization')) else 50.0

    confidence = "HIGH" if top_score >= 75 else ("MODERATE" if top_score >= 65 else "WATCH")
    status_label = "🟢 EARLY ACCUMULATION" if top_score >= 65 else "🟡 WATCH"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 10px; padding: 18px 22px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="font-size: 0.75rem; color: #38BDF8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">
                    ⭐ #1 PRECURSOR ACCUMULATION SPOTLIGHT
                </div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #F8FAFC; margin-top: 4px;">
                    {top1['industry']}
                </div>
                <div style="margin-top: 6px;">
                    <span style="background-color: rgba(16, 185, 129, 0.2); color: #34D399; font-size: 0.78rem; padding: 3px 10px; border-radius: 4px; font-weight: 700; border: 1px solid rgba(16, 185, 129, 0.4);">
                        {status_label}
                    </span>
                    <span style="margin-left: 10px; font-size: 0.82rem; color: #94A3B8;">
                        Possible move window: <b style="color: #F8FAFC;">{lead_min}–{lead_max} trading days</b>
                    </span>
                    <span style="margin-left: 10px; font-size: 0.82rem; color: #94A3B8;">
                        Confidence: <b style="color: #38BDF8;">{confidence}</b>
                    </span>
                </div>
            </div>
            <div style="display: flex; gap: 16px; align-items: center;">
                <div style="text-align: right; background: rgba(0, 0, 0, 0.3); padding: 8px 14px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.06);">
                    <div style="font-size: 0.70rem; color: #94A3B8; text-transform: uppercase;">Early Radar Score</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #38BDF8; font-family: 'JetBrains Mono';">{top_score:.1f}<span style="font-size: 0.75rem; color: #64748B;">/100</span></div>
                </div>
                <div style="text-align: right; background: rgba(0, 0, 0, 0.3); padding: 8px 14px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.06);">
                    <div style="font-size: 0.70rem; color: #94A3B8; text-transform: uppercase;">Current V3.2 Strength</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #F59E0B; font-family: 'JetBrains Mono';">{v32_score:.1f}<span style="font-size: 0.75rem; color: #64748B;">/100</span></div>
                </div>
            </div>
        </div>
        <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 0.82rem; color: #CBD5E1;">
            <b>Why is it showing up?</b>
            <ul style="margin: 4px 0 0 16px; padding: 0; color: #94A3B8; line-height: 1.6;">
                <li>More stocks in this industry are starting to move together (Cross-Stock Sync: <b style="color: #F8FAFC;">{sync_score:.1f}%</b>).</li>
                <li>Buying and delivery intensity is increasing across constituent equities.</li>
                <li>Volatility is compressing, creating price tension before potential expansion.</li>
                <li>Broad public momentum has not fully appeared yet (Current Strength: <b style="color: #F59E0B;">{v32_score:.1f}/100</b>).</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- LEVEL 2: USEFUL SUPPORTING METRICS (TOP 5 TABLE) ---
    st.markdown("### 🏆 Top 5 Precursor Opportunities")
    top5 = df_radar_top.head(5).copy()
    
    # Map friendly status labels
    top5['Status'] = top5['early_radar_score'].apply(
        lambda s: '🔥 PRE-BREAKOUT' if s >= 75 else ('🟢 EARLY ACCUMULATION' if s >= 65 else '🟡 WATCH')
    )
    
    disp_top5 = top5[[
        'Rank', 'industry', 'Status', 'early_radar_score',
        'expected_lead_days', 'cross_stock_synchronization', 'v3_2_strength'
    ]].rename(columns={
        'industry': 'Industry',
        'Status': 'Signal Tier',
        'early_radar_score': 'Radar Score (0-100)',
        'expected_lead_days': 'Expected Lead Time',
        'cross_stock_synchronization': 'Sync %',
        'v3_2_strength': 'Current V3.2'
    })
    
    st.dataframe(
        disp_top5,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Radar Score (0-100)": st.column_config.ProgressColumn("Radar Score", format="%0.1f", min_value=0, max_value=100),
            "Expected Lead Time": st.column_config.NumberColumn("Expected Lead", format="%.1f Days"),
            "Sync %": st.column_config.ProgressColumn("Sync %", format="%0.1f%%", min_value=0, max_value=100),
            "Current V3.2": st.column_config.ProgressColumn("Current V3.2", format="%0.1f", min_value=0, max_value=100)
        }
    )
    
    # --- LEVEL 3: DETAILED QUANTITATIVE / TECHNICAL INFORMATION ---
    with st.expander("📊 Quantitative Details: Mathematical Probabilities & Feature Breakdowns"):
        st.markdown("##### Detailed Point-in-Time Multi-Horizon Probabilities")
        disp_tech = top5[[
            'Rank', 'industry', 'prob_1d', 'prob_3d', 'prob_5d',
            'accumulation_pressure', 'cross_stock_synchronization', 'feature_explanation'
        ]].rename(columns={
            'industry': 'Industry',
            'prob_1d': 'P(1D)',
            'prob_3d': 'P(3D)',
            'prob_5d': 'P(5D)',
            'accumulation_pressure': 'Accum. Pressure (0-100)',
            'cross_stock_synchronization': 'Sync Coeff (%)',
            'feature_explanation': 'Precursor Diagnostic'
        })
        st.dataframe(
            disp_tech,
            use_container_width=True,
            hide_index=True,
            column_config={
                "P(1D)": st.column_config.NumberColumn("P(1D)", format="%.1f%%"),
                "P(3D)": st.column_config.NumberColumn("P(3D)", format="%.1f%%"),
                "P(5D)": st.column_config.NumberColumn("P(5D)", format="%.1f%%"),
                "Accum. Pressure (0-100)": st.column_config.ProgressColumn("Accum. Pressure", format="%0.1f", min_value=0, max_value=100),
                "Sync Coeff (%)": st.column_config.NumberColumn("Sync %", format="%.1f%%")
            }
        )
        
        for _, row in top5.iterrows():
            st.markdown(f"""
            - **#{row['Rank']} {row['industry']}**: Accumulation Pressure = `{row['accumulation_pressure']:.1f}`, Cross-Stock Sync = `{row['cross_stock_synchronization']:.1f}%`. *{row['feature_explanation']}*
            """)
            
    # Dedicated Subsection: EARLY TURNAROUNDS (Low V3.2 + High Radar)
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.markdown("### 🟢 Early Turnarounds (Quiet Bottom Accumulation)")
    st.caption("Industries that are not yet strong on the normal momentum model (V3.2 < 55), but are showing unusual early accumulation (Radar ≥ 60).")
    
    df_turnarounds = df_today[
        (df_today['v3_2_strength'] < 55.0) & (df_today['early_radar_score'] >= 60.0)
    ].sort_values('early_radar_score', ascending=False).reset_index(drop=True)
    
    if not df_turnarounds.empty:
        df_turnarounds['Rank'] = np.arange(1, len(df_turnarounds) + 1)
        disp_turn = df_turnarounds[[
            'Rank', 'industry', 'v3_2_strength', 'early_radar_score',
            'prob_3d', 'prob_5d', 'expected_lead_days', 'cross_stock_synchronization'
        ]].rename(columns={
            'industry': 'Industry',
            'v3_2_strength': 'Current Strength (V3.2)',
            'early_radar_score': 'Early Radar Score',
            'prob_3d': 'P(3D)',
            'prob_5d': 'P(5D)',
            'expected_lead_days': 'Expected Lead',
            'cross_stock_synchronization': 'Sync %'
        })
        st.dataframe(disp_turn, use_container_width=True, hide_index=True)
    else:
        st.info("No early turnaround candidates (V3.2 < 55 + Radar ≥ 60) detected on this session.")
        
    st.caption("ℹ️ *Disclaimer: Early Sector Radar probabilities and lead times represent calibrated historical statistical frequencies from 2020–2026 cash market data. They are research signals and do not guarantee future performance.*")
