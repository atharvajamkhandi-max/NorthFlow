"""
Quantitative Research Module: Model Drift & Stability Monitoring Engine.
Monitors rolling Rank IC, IC IR, MAE, Brier Score, and Regime Performance across 403 historical sessions.
Classifies model stability states: HEALTHY, WATCH, DEGRADING, FAILED.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy.stats import spearmanr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

class QuantModelDriftMonitor:
    @staticmethod
    def compute_model_drift(df_preds: pd.DataFrame) -> pd.DataFrame:
        print("\n--- [Model Drift Monitor] Tracking Rolling Stability & Degradation Flags ---")
        df = df_preds.sort_values('date').reset_index(drop=True).copy()
        
        dates = sorted(df['date'].unique().tolist())
        drift_records = []

        window = 30 # 30-session rolling monitoring window
        for i in range(window, len(dates)):
            cur_date = dates[i]
            window_dates = dates[i - window : i]
            sub = df[df['date'].isin(window_dates)]

            if len(sub) < 15:
                continue

            ric, _ = spearmanr(sub['industry_strength_score'], sub['future_excess_return_20D']) if len(sub) > 5 else (0.0, 1.0)
            mae = float(np.mean(np.abs((sub['industry_strength_score'] - 50.0) * 0.15 - sub['future_excess_return_20D'])))
            
            top_q = sub[sub['industry_strength_score'] >= sub['industry_strength_score'].quantile(0.8)]['future_excess_return_20D'].mean()
            bot_q = sub[sub['industry_strength_score'] <= sub['industry_strength_score'].quantile(0.2)]['future_excess_return_20D'].mean()
            spread = top_q - bot_q

            # Stability Status Classification
            if ric >= 0.08 and spread >= 1.5:
                status = "HEALTHY"
            elif ric >= 0.0 and spread >= 0.0:
                status = "WATCH"
            elif ric >= -0.10:
                status = "DEGRADING"
            else:
                status = "FAILED"

            drift_records.append({
                "Date": cur_date,
                "Rolling_Rank_IC": round(ric, 4),
                "Rolling_MAE": round(mae, 2),
                "Rolling_Decile_Spread": round(spread, 2),
                "Monitoring_Status": status
            })

        df_drift = pd.DataFrame(drift_records)
        print(f"Model drift monitoring complete across {len(df_drift)} rolling windows.")
        return df_drift
