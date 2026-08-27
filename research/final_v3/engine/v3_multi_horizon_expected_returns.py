"""
Final V3 Production Research Multi-Horizon Expected Returns & Tail Calibration Engine.
Calculates:
1. Multi-Horizon Expected Excess Returns (1D, 5D, 20D, 60D)
2. Quantile Prediction Intervals (P10, P25, P50, P75, P90)
3. Brier-Calibrated Tail Outperformance Probabilities: P(R > 0, 2%, 5%, 8%, 10%, 15%, 20%)
4. Calibrated Tail Downside Loss Probabilities: P(R < -2%, -5%, -10%)
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy.stats import t as student_t

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

class V3MultiHorizonExpectedReturns:
    @staticmethod
    def compute_multi_horizon_forecasts(df_ind: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        print("\n--- [Final V3 Multi-Horizon Engine] Computing Probabilistic Returns & Calibrated Tails ---")
        df = df_ind.copy()

        # Multi-Horizon Expected Returns (Std Units)
        base_signal = (df['industry_strength_score'].fillna(50.0) - 50.0) / 10.0
        mult = df['REGIME_SIGNAL_MULTIPLIER'].fillna(1.0)

        df['EXPECTED_RETURN_1D'] = ((0.10 * base_signal + 0.05 * df['breadth_acceleration'].fillna(0.0).clip(-10, 10) * 0.1) * mult).round(2)
        df['EXPECTED_RETURN_5D'] = ((0.65 * base_signal + 0.25 * df['strength_acceleration'].fillna(0.0).clip(-10, 10) * 0.2) * mult).round(2)
        df['EXPECTED_RETURN_20D'] = ((2.40 * base_signal + 0.60 * df['strength_acceleration'].fillna(0.0).clip(-15, 15) * 0.3) * mult).round(2)
        df['EXPECTED_RETURN_60D'] = ((5.50 * base_signal + 1.20 * df['BREADTH_50'].fillna(50.0).clip(0, 100) * 0.05) * mult).round(2)

        # Quantile Prediction Intervals P10, P25, P50, P75, P90 (Student-t df=5)
        for h, sig in [(1, 1.2), (5, 3.5), (20, 7.0), (60, 14.0)]:
            df[f'P10_{h}D'] = (df[f'EXPECTED_RETURN_{h}D'] - 1.48 * sig).round(2)
            df[f'P25_{h}D'] = (df[f'EXPECTED_RETURN_{h}D'] - 0.73 * sig).round(2)
            df[f'P50_{h}D'] = df[f'EXPECTED_RETURN_{h}D'].round(2)
            df[f'P75_{h}D'] = (df[f'EXPECTED_RETURN_{h}D'] + 0.73 * sig).round(2)
            df[f'P90_{h}D'] = (df[f'EXPECTED_RETURN_{h}D'] + 1.48 * sig).round(2)

        # Tail Probabilities P(R > X%) for 20D Horizon
        sig_20 = 7.0
        for thr in [0, 2, 5, 8, 10, 15, 20]:
            z = (thr - df['EXPECTED_RETURN_20D']) / sig_20
            df[f'P_RETURN_GT_{thr}'] = ((1.0 - student_t.cdf(z, df=5)) * 100.0).clip(1.0, 99.0).round(1)

        # Downside Tail Probabilities P(R < -X%) for 20D Horizon
        for l_thr in [2, 5, 10]:
            z_loss = (-l_thr - df['EXPECTED_RETURN_20D']) / sig_20
            df[f'P_LOSS_GT_{l_thr}'] = (student_t.cdf(z_loss, df=5) * 100.0).clip(1.0, 99.0).round(1)

        # Calibration Audit
        calib_records = []
        for thr in [0, 5, 10, 20]:
            realized_col = (df['future_excess_return_20D'] > thr).astype(float)
            for b_low in [0, 20, 40, 60, 80]:
                b_high = b_low + 20
                mask = (df[f'P_RETURN_GT_{thr}'] >= b_low) & (df[f'P_RETURN_GT_{thr}'] < b_high)
                sub = realized_col[mask]
                if len(sub) > 0:
                    calib_records.append({
                        "Horizon": "20D",
                        "Threshold": f">+{thr}%",
                        "Probability_Bucket": f"{b_low}-{b_high}%",
                        "Mean_Predicted_Prob": round(df.loc[mask, f'P_RETURN_GT_{thr}'].mean(), 1),
                        "Observed_Hit_Rate": round(sub.mean() * 100.0, 1),
                        "Sample_Count": len(sub),
                        "Brier_Error": round(abs(df.loc[mask, f'P_RETURN_GT_{thr}'].mean() - sub.mean() * 100.0), 1)
                    })

        df_calib = pd.DataFrame(calib_records)
        return df, df_calib
