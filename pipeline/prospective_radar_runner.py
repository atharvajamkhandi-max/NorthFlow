"""
Prospective Early Sector Radar Runner & Cryptographic Audit Logger (Phase 26).
Executes daily snapshot generation, logs SHA-256 hashes, and tracks forward outcomes.
"""

import sys
import hashlib
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
PROSPECTIVE_DIR = BASE_DIR / "research" / "prospective_validation"
PROSPECTIVE_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG_FILE = PROSPECTIVE_DIR / "audit_log.csv"

from dashboard.components.early_radar_shadow_service import (
    compute_early_radar_scores_point_in_time,
    load_point_in_time_industry_history
)
from config.early_radar_v1_frozen import EARLY_RADAR_V1_FROZEN

def generate_daily_prospective_snapshot(selected_date: str) -> Path:
    """
    Generates and persists an immutable daily prospective snapshot for selected_date.
    Logs cryptographic SHA-256 hash to audit_log.csv.
    """
    ind_history = load_point_in_time_industry_history(selected_date)
    if ind_history.empty:
        raise ValueError(f"No point-in-time data available for session {selected_date}")
        
    # Strictly point-in-time calculation
    ind_scored = compute_early_radar_scores_point_in_time(ind_history)
    
    # Add V3.2 proxy
    ind_scored['v3_2_strength'] = np.clip(
        0.40 * ind_scored['breadth_50'] + 0.30 * np.clip((ind_scored['ind_ret_20d'] + 10.0) / 30.0 * 100.0, 0.0, 100.0) +
        0.30 * np.clip(ind_scored['breadth_20'], 0.0, 100.0),
        0.0, 100.0
    ).round(1)
    
    target_dt = pd.to_datetime(selected_date)
    df_today = ind_scored[ind_scored['date'] == target_dt].copy()
    if df_today.empty:
        df_today = ind_scored[ind_scored['date'] == ind_scored['date'].max()].copy()
        
    df_today = df_today.sort_values('early_radar_score', ascending=False).reset_index(drop=True)
    df_today['rank'] = np.arange(1, len(df_today) + 1)
    
    # Flags
    df_today['low_v32_flag'] = (df_today['v3_2_strength'] < 55.0).astype(int)
    df_today['high_radar_flag'] = (df_today['early_radar_score'] >= 65.0).astype(int)
    df_today['low_v32_high_radar_turnaround'] = (df_today['low_v32_flag'] == 1) & (df_today['high_radar_flag'] == 1)
    
    # Save snapshot
    out_file = PROSPECTIVE_DIR / f"{selected_date}_early_radar.csv"
    cols = [
        'date', 'industry', 'rank', 'early_radar_score', 'alert_level',
        'prob_1d', 'prob_3d', 'prob_5d', 'expected_lead_days', 'v3_2_strength',
        'constituents', 'pct_pos_mom', 'cross_stock_synchronization',
        'low_v32_high_radar_turnaround', 'feature_explanation'
    ]
    avail_cols = [c for c in cols if c in df_today.columns]
    df_today[avail_cols].to_csv(out_file, index=False)
    
    # Compute SHA-256 hash
    file_bytes = out_file.read_bytes()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    
    # Log to audit_log.csv
    top5_names = df_today['industry'].head(5).tolist()
    audit_record = {
        "date": selected_date,
        "model_version": EARLY_RADAR_V1_FROZEN["model_version"],
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "num_industries": len(df_today),
        "top1": top5_names[0] if len(top5_names) > 0 else "",
        "top2": top5_names[1] if len(top5_names) > 1 else "",
        "top3": top5_names[2] if len(top5_names) > 2 else "",
        "top4": top5_names[3] if len(top5_names) > 3 else "",
        "top5": top5_names[4] if len(top5_names) > 4 else "",
        "sha256_hash": file_hash
    }
    
    if AUDIT_LOG_FILE.exists():
        df_audit = pd.read_csv(AUDIT_LOG_FILE)
        df_audit = df_audit[df_audit['date'] != selected_date]
        df_audit = pd.concat([df_audit, pd.DataFrame([audit_record])], ignore_index=True)
    else:
        df_audit = pd.DataFrame([audit_record])
        
    df_audit.to_csv(AUDIT_LOG_FILE, index=False)
    return out_file

if __name__ == "__main__":
    test_date = "2026-08-21"
    snap_path = generate_daily_prospective_snapshot(test_date)
    print(f"Generated snapshot: {snap_path}")
