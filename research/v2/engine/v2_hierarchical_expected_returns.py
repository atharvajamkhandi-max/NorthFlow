"""
Phase V2 Hierarchical Expected Return Decomposition & Tail Probability Engine.
Calculates:
1. Hierarchical Decomposition: E[R_stock] = E[R_mkt] + E[R_sec|mkt] + E[R_ind|sec] + E[R_stock|ind]
2. Multi-Horizon Expected Excess Returns (1D, 5D, 20D, 60D)
3. Prediction Intervals P10, P25, P50, P75, P90
4. Brier Tail Probabilities: P(R > 0), P(R > 2%), P(R > 5%), P(R > 8%), P(R > 10%), P(R > 15%), P(R > 20%)
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy.stats import t as student_t

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

class V2HierarchicalExpectedReturns:
    @staticmethod
    def compute_hierarchical_forecasts(df_full_ind: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        print("\n--- [V2 Hierarchical Expected Returns] Decomposing Multi-Horizon Alpha ---")
        df = df_full_ind.copy()

        # Multi-Horizon Expected Returns
        base_signal = (df['industry_strength_score'].fillna(50.0) - 50.0) / 10.0 # Std units
        
        df['MarketContribution'] = (0.35 * base_signal).round(2)
        df['SectorContribution'] = (0.25 * base_signal).round(2)
        df['IndustryContribution'] = (1.40 * base_signal + 0.40 * df['strength_acceleration'].fillna(0.0).clip(-15, 15) * 0.2).round(2)
        df['StockContribution'] = (0.80 * base_signal).round(2)

        # Expected Returns across Horizons 1D, 5D, 20D, 60D
        df['ExpectedReturn_1D'] = (0.10 * base_signal + 0.05 * df['breadth_acceleration'].fillna(0.0).clip(-10, 10) * 0.1).round(2)
        df['ExpectedReturn_5D'] = (0.65 * base_signal + 0.25 * df['strength_acceleration'].fillna(0.0).clip(-10, 10) * 0.2).round(2)
        df['ExpectedReturn_20D'] = (df['MarketContribution'] + df['SectorContribution'] + df['IndustryContribution'] + df['StockContribution']).round(2)
        df['ExpectedReturn_60D'] = (5.50 * base_signal + 1.20 * df['breadth_50'].fillna(50.0).clip(0, 100) * 0.05).round(2)

        # Prediction Intervals P10, P25, P50, P75, P90 (Student-t df=5 residual dispersion)
        for h, sig in [(1, 1.2), (5, 3.5), (20, 7.0), (60, 14.0)]:
            df[f'P10_{h}D'] = (df[f'ExpectedReturn_{h}D'] - 1.48 * sig).round(2)
            df[f'P25_{h}D'] = (df[f'ExpectedReturn_{h}D'] - 0.73 * sig).round(2)
            df[f'P50_{h}D'] = df[f'ExpectedReturn_{h}D'].round(2)
            df[f'P75_{h}D'] = (df[f'ExpectedReturn_{h}D'] + 0.73 * sig).round(2)
            df[f'P90_{h}D'] = (df[f'ExpectedReturn_{h}D'] + 1.48 * sig).round(2)

        # Tail Probabilities P(R > X%) for 20D Horizon
        sig_20 = 7.0
        for thr in [0, 2, 5, 8, 10, 15, 20]:
            z = (thr - df['ExpectedReturn_20D']) / sig_20
            df[f'P_gt_{thr}pct_20D'] = ((1.0 - student_t.cdf(z, df=5)) * 100.0).clip(1.0, 99.0).round(1)

        # Opportunity Class
        conds_opp = [
            (df['industry_strength_score'] >= 75.0) & (df['strength_acceleration'] >= 2.0),
            (df['industry_strength_score'] >= 65.0),
            (df['strength_acceleration'] >= 6.0) & (df['industry_strength_score'] >= 45.0),
            (df['NetPressure'] >= 25.0),
            (df['industry_strength_score'] < 35.0) & (df['strength_acceleration'] <= -4.0),
            (df['industry_strength_score'] < 35.0),
            (df['strength_acceleration'] <= -6.0)
        ]
        choices_opp = [
            'LEADING',
            'ESTABLISHED_LEADER',
            'EMERGING_LEADER',
            'ACCUMULATION',
            'DISTRIBUTION',
            'LAGGING',
            'WEAKENING'
        ]
        df['OpportunityClass'] = np.select(conds_opp, choices_opp, default='NEUTRAL')

        # Model Agreement Score (0 to 100)
        df['ModelAgreementScore'] = (100.0 - df['ensemble_dispersion'].fillna(1.0).clip(0, 5) * 15.0).clip(20, 100).round(1)

        # Final Quant Score (0 to 100)
        df['FinalQuantScore'] = (
            0.35 * df['industry_strength_score'] +
            0.30 * (df['ExpectedReturn_20D'].clip(-10, 15) * 4.0 + 40.0) +
            0.15 * df['P_gt_5pct_20D'] +
            0.10 * df['ModelAgreementScore'] +
            0.10 * (df['NetPressure'].clip(-50, 50) * 0.5 + 50.0)
        ).clip(0, 100).round(1)

        # Probability Calibration Audit
        calib_records = []
        for thr in [0, 5, 10, 20]:
            realized_col = (df['future_excess_return_20D'] > thr).astype(float)
            for b_low in [0, 20, 40, 60, 80]:
                b_high = b_low + 20
                mask = (df[f'P_gt_{thr}pct_20D'] >= b_low) & (df[f'P_gt_{thr}pct_20D'] < b_high)
                sub = realized_col[mask]
                if len(sub) > 0:
                    calib_records.append({
                        "Horizon": "20D",
                        "Threshold": f">+{thr}%",
                        "Probability_Bucket": f"{b_low}-{b_high}%",
                        "Mean_Predicted_Prob": round(df.loc[mask, f'P_gt_{thr}pct_20D'].mean(), 1),
                        "Observed_Hit_Rate": round(sub.mean() * 100.0, 1),
                        "Sample_Count": len(sub),
                        "Brier_Error": round(abs(df.loc[mask, f'P_gt_{thr}pct_20D'].mean() - sub.mean() * 100.0), 1)
                    })

        df_calib = pd.DataFrame(calib_records)
        print(f"Hierarchical expected return decomposition and probability calibration complete ({len(df_calib)} buckets).")
        return df, df_calib
