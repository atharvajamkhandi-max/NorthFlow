"""
Phase D & E: Observable Accumulation & Distribution Pressure Engine.
Computes empirical pressure scores from observable price, volume, delivery, breadth, and breakout persistence.
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

class QuantAccumulationEngine:
    @staticmethod
    def compute_accumulation_distribution(df_ind: pd.DataFrame) -> pd.DataFrame:
        print("Computing observable accumulation and distribution pressure scores...")
        df = df_ind.copy()
        
        # 1. Positive Relative Return component (0 to 100)
        pos_ret_comp = (df['industry_RS_market'].clip(-20, 20) * 2.5 + 50.0).clip(0, 100)
        
        # 2. Volume Strength component (0 to 100)
        vol_comp = (df['volume_strength'].clip(0, 3) * 33.33).clip(0, 100)
        
        # 3. Breadth Expansion component (0 to 100)
        breadth_comp = (df['breadth_acceleration'].clip(-30, 30) * 1.66 + 50.0).clip(0, 100)
        
        # 4. Delivery Confirmation component (0 to 100)
        deliv_comp = df['avg_delivery_pct'].clip(0, 100)
        
        # 5. Trend Stacking Breadth component (0 to 100)
        trend_comp = df['trend_stack_breadth'].clip(0, 100)

        # Observable Accumulation Pressure Score (0-100)
        df['ACCUMULATION_PRESSURE_SCORE'] = (
            0.25 * pos_ret_comp +
            0.25 * vol_comp +
            0.20 * breadth_comp +
            0.15 * trend_comp +
            0.15 * deliv_comp
        ).round(2)

        # Observable Distribution Pressure Score (0-100)
        neg_ret_comp = 100.0 - pos_ret_comp
        breadth_contr_comp = 100.0 - breadth_comp
        df['DISTRIBUTION_PRESSURE_SCORE'] = (
            0.35 * neg_ret_comp +
            0.30 * breadth_contr_comp +
            0.20 * vol_comp + # High volume on negative return
            0.15 * (100.0 - trend_comp)
        ).round(2)

        return df
