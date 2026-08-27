"""
Phase V2 Observable Accumulation / Distribution Engine.
Constructs:
1. AccumulationScore (0-100) & DistributionScore (0-100)
2. NetPressure = AccumulationScore - DistributionScore (-100 to +100)
3. 5 Observable States: STRONG_DISTRIBUTION, DISTRIBUTION, NEUTRAL, ACCUMULATION, STRONG_ACCUMULATION
4. Calibrated P(Accumulation) & P(Distribution)
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

class V2AccumulationEngine:
    @staticmethod
    def compute_accumulation_states(df_ind: pd.DataFrame) -> pd.DataFrame:
        print("Computing V2 5-state accumulation/distribution pressure model...")
        df = df_ind.copy()

        # Component 1: Relative Return vs NIFTY (0 to 100)
        pos_ret_comp = (df['industry_RS_market'].clip(-20, 20) * 2.5 + 50.0).clip(0, 100)
        
        # Component 2: Volume Strength (0 to 100)
        vol_comp = (df['volume_strength'].clip(0, 3) * 33.33).clip(0, 100)
        
        # Component 3: Breadth Acceleration (0 to 100)
        breadth_comp = (df['breadth_acceleration'].clip(-30, 30) * 1.66 + 50.0).clip(0, 100)
        
        # Component 4: Delivery Confirmation (0 to 100)
        deliv_comp = df['avg_delivery_pct'].clip(0, 100)
        
        # Component 5: Trend Stacking (0 to 100)
        trend_comp = df['trend_stack_breadth'].clip(0, 100)

        # Accumulation Score (0 to 100)
        df['AccumulationScore'] = (
            0.25 * pos_ret_comp +
            0.25 * vol_comp +
            0.20 * breadth_comp +
            0.15 * trend_comp +
            0.15 * deliv_comp
        ).round(1)

        # Distribution Score (0 to 100)
        neg_ret_comp = 100.0 - pos_ret_comp
        breadth_contr_comp = 100.0 - breadth_comp
        df['DistributionScore'] = (
            0.35 * neg_ret_comp +
            0.30 * breadth_contr_comp +
            0.20 * vol_comp +
            0.15 * (100.0 - trend_comp)
        ).round(1)

        # Net Pressure (-100 to +100)
        df['NetPressure'] = (df['AccumulationScore'] - df['DistributionScore']).round(1)

        # Probabilities P(Accumulation) and P(Distribution)
        df['P_Accumulation'] = (df['AccumulationScore'] / np.maximum(1.0, df['AccumulationScore'] + df['DistributionScore']) * 100.0).round(1)
        df['P_Distribution'] = (100.0 - df['P_Accumulation']).round(1)

        # 5 Observable States
        conds_5state = [
            (df['NetPressure'] >= 35.0),
            (df['NetPressure'] >= 10.0),
            (df['NetPressure'] <= -35.0),
            (df['NetPressure'] <= -10.0)
        ]
        choices_5state = [
            '4_STRONG_ACCUMULATION',
            '3_ACCUMULATION',
            '0_STRONG_DISTRIBUTION',
            '1_DISTRIBUTION'
        ]
        df['ACCUMULATION_STATE'] = np.select(conds_5state, choices_5state, default='2_NEUTRAL')

        return df
