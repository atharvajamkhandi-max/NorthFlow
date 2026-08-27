"""
Isolated Research Prediction Logger Database Engine.
Creates and maintains research/data/prediction_log.db storing:
- prediction_date, industry, model_version, strength_score, strength_rank
- probability_5d, probability_10d, probability_20d
- expected_return_5d, expected_return_10d, expected_return_20d
- confidence, constituent_count, effective_constituents, concentration, market_regime
- forward realized returns (realized_return_5d, realized_relative_return_5d, etc.)
"""

import sqlite3
import pandas as pd
import os
from typing import Dict, Any, List

DB_PATH = r"C:\Users\athar\.gemini\antigravity\scratch\industry-money-flow\research\data\prediction_log.db"

def init_prediction_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS industry_predictions (
            prediction_date TEXT NOT NULL,
            basic_industry TEXT NOT NULL,
            model_version TEXT NOT NULL,
            strength_score REAL,
            strength_rank INTEGER,
            probability_5d REAL,
            probability_10d REAL,
            probability_20d REAL,
            expected_return_5d REAL,
            expected_return_10d REAL,
            expected_return_20d REAL,
            model_confidence REAL,
            constituent_count INTEGER,
            effective_constituents REAL,
            concentration_top3 REAL,
            market_regime TEXT,
            realized_return_5d REAL,
            realized_relative_return_5d REAL,
            PRIMARY KEY (prediction_date, basic_industry, model_version)
        );
        """)
    conn.close()

def log_predictions(df_scored: pd.DataFrame):
    init_prediction_db()
    conn = sqlite3.connect(DB_PATH)
    
    rows_to_insert = []
    for d, grp in df_scored.groupby('date'):
        grp_ranked = grp.sort_values('ENSEMBLE_Prediction', ascending=False).reset_index(drop=True)
        for rank_idx, r in grp_ranked.iterrows():
            rows_to_insert.append((
                r['date'],
                r['basic_industry'],
                'RESEARCH_V2_ENSEMBLE',
                r.get('ENSEMBLE_Prediction', 50.0),
                rank_idx + 1,
                r.get('ML_GradientBoosting_P5', 0.50),
                0.50, # 10D placeholder
                0.50, # 20D placeholder
                r.get('ML_GradientBoosting_Ret5', 0.0),
                0.0,
                0.0,
                r.get('herfindahl_index', 0.50),
                int(r.get('stock_count', 1)),
                r.get('effective_constituents', 1.0),
                r.get('top3_contrib_pct', 100.0),
                'ROTATION',
                r.get('fwd_ret_5d', None),
                r.get('rel_fwd_5d', None)
            ))

    with conn:
        conn.executemany("""
        INSERT OR REPLACE INTO industry_predictions VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        );
        """, rows_to_insert)
    conn.close()
    print(f"Logged {len(rows_to_insert)} prediction records into {DB_PATH}")
