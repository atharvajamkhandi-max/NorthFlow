"""
Forensic Session Audit & Independent Time-Series Verification Engine.
Generates research/results/session_audit.csv
"""

import os
import sqlite3
import pandas as pd
import numpy as np

def run_session_audit(db_path: str, results_dir: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    
    # Query distinct dates from daily_prices
    dates = pd.read_sql_query("SELECT DISTINCT date FROM daily_prices ORDER BY date ASC;", conn)['date'].tolist()
    
    session_records = []
    total_dates = len(dates)

    for idx, d in enumerate(dates):
        # Stock count on date
        n_stocks = conn.execute("SELECT COUNT(DISTINCT symbol) FROM daily_prices WHERE date = ?;", [d]).fetchone()[0]
        
        # Industry count on date
        q_ind = """
            SELECT COUNT(DISTINCT s.basic_industry) 
            FROM daily_prices dp
            JOIN stocks s ON dp.symbol = s.symbol
            WHERE dp.date = ? AND s.basic_industry != 'UNKNOWN' AND s.active = 1;
        """
        n_inds = conn.execute(q_ind, [d]).fetchone()[0]
        
        # Forward observations availability
        has_fwd_5d = 1 if (idx + 5) < total_dates else 0
        has_fwd_10d = 1 if (idx + 10) < total_dates else 0
        has_fwd_20d = 1 if (idx + 20) < total_dates else 0

        # Non-overlapping indicators
        is_non_overlap_5d = 1 if (idx % 5 == 0 and has_fwd_5d == 1) else 0
        is_non_overlap_10d = 1 if (idx % 10 == 0 and has_fwd_10d == 1) else 0
        is_non_overlap_20d = 1 if (idx % 20 == 0 and has_fwd_20d == 1) else 0

        session_records.append({
            'Session_Index': idx + 1,
            'Date': d,
            'Stocks_Count': n_stocks,
            'Industries_Count': n_inds,
            'Valid_Industry_Obs': n_inds,
            'Missing_Industry_Obs': max(0, 135 - n_inds),
            'Has_Forward_5D': has_fwd_5d,
            'Has_Forward_10D': has_fwd_10d,
            'Has_Forward_20D': has_fwd_20d,
            'Is_Non_Overlapping_5D': is_non_overlap_5d,
            'Is_Non_Overlapping_10D': is_non_overlap_10d,
            'Is_Non_Overlapping_20D': is_non_overlap_20d
        })

    conn.close()
    df_audit = pd.DataFrame(session_records)

    output_csv = os.path.join(results_dir, "session_audit.csv")
    df_audit.to_csv(output_csv, index=False)
    print(f"Session audit saved to: {output_csv}")

    # Summary statistics
    total_sessions = len(df_audit)
    fwd_5_sessions = df_audit['Has_Forward_5D'].sum()
    fwd_10_sessions = df_audit['Has_Forward_10D'].sum()
    fwd_20_sessions = df_audit['Has_Forward_20D'].sum()
    non_overlap_5_count = df_audit['Is_Non_Overlapping_5D'].sum()
    non_overlap_10_count = df_audit['Is_Non_Overlapping_10D'].sum()
    non_overlap_20_count = df_audit['Is_Non_Overlapping_20D'].sum()

    print(f"Total Trading Sessions: {total_sessions}")
    print(f"Sessions with Forward 5D: {fwd_5_sessions} (Non-overlapping: {non_overlap_5_count})")
    print(f"Sessions with Forward 10D: {fwd_10_sessions} (Non-overlapping: {non_overlap_10_count})")
    print(f"Sessions with Forward 20D: {fwd_20_sessions} (Non-overlapping: {non_overlap_20_count})")

    return df_audit
