"""
Final V3 Production Research Signal State & Observable Accumulation Engine.
Constructs:
1. Signal Lifecycle Engine (5 States: NEW, DEVELOPING, MATURE, EXHAUSTED, REVERSING)
   - SIGNAL_AGE, SIGNAL_PERSISTENCE, SIGNAL_DECAY, SIGNAL_EXHAUSTION_RISK
2. Observable Accumulation / Distribution Engine (3 States: ACCUMULATION, NEUTRAL, DISTRIBUTION)
   - AccumulationScore (0-100), DistributionScore (0-100), NetPressure (-100 to +100)
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

class V3SignalStateAndAccum:
    @staticmethod
    def compute_signal_state_and_accumulation(df_ind: pd.DataFrame) -> pd.DataFrame:
        print("Computing Signal Lifecycle (5 States) and Observable Accumulation Pressure (3 States)...")
        df = df_ind.copy()

        # 1. Observable Accumulation / Distribution Pressure
        pos_ret_comp = (df['industry_RS_market'].clip(-20, 20) * 2.5 + 50.0).clip(0, 100)
        vol_comp = (df['volume_strength'].clip(0, 3) * 33.33).clip(0, 100)
        breadth_comp = (df['breadth_acceleration'].clip(-30, 30) * 1.66 + 50.0).clip(0, 100)
        trend_comp = df['trend_stack_breadth'].clip(0, 100)
        deliv_comp = df['avg_delivery_pct'].clip(0, 100)

        df['AccumulationScore'] = (
            0.25 * pos_ret_comp + 0.25 * vol_comp + 0.20 * breadth_comp + 0.15 * trend_comp + 0.15 * deliv_comp
        ).round(1)

        neg_ret_comp = 100.0 - pos_ret_comp
        df['DistributionScore'] = (
            0.35 * neg_ret_comp + 0.30 * (100.0 - breadth_comp) + 0.20 * vol_comp + 0.15 * (100.0 - trend_comp)
        ).round(1)

        df['NetPressure'] = (df['AccumulationScore'] - df['DistributionScore']).round(1)
        df['ACCUMULATION_STATE'] = np.where(df['NetPressure'] >= 15.0, 'ACCUMULATION', np.where(df['NetPressure'] <= -15.0, 'DISTRIBUTION', 'NEUTRAL'))

        # 2. Signal Lifecycle & State Engine
        # Signal Persistence: Rolling consecutive sessions with Strength >= 65
        is_strong = (df['industry_strength_score'] >= 65.0).astype(int)
        df['SIGNAL_AGE'] = df.groupby('basic_industry')['industry_strength_score'].transform(lambda x: (x >= 65.0).cumsum() - (x >= 65.0).cumsum().where(~(x >= 65.0)).ffill().fillna(0)).astype(int)
        
        # Signal Decay / Acceleration
        df['SIGNAL_ACCELERATION'] = df['strength_acceleration']
        df['SIGNAL_DECAY'] = np.where((df['SIGNAL_AGE'] >= 15) & (df['SIGNAL_ACCELERATION'] < 0), 1, 0)
        df['SIGNAL_EXHAUSTION_RISK'] = np.where((df['industry_strength_score'] >= 85.0) & (df['SIGNAL_AGE'] >= 20), 'HIGH', 'LOW')

        # 5 Signal States: NEW, DEVELOPING, MATURE, EXHAUSTED, REVERSING
        conds_sig = [
            (df['SIGNAL_AGE'] >= 20) & (df['strength_acceleration'] < -3.0),
            (df['industry_strength_score'] >= 80.0) & (df['SIGNAL_AGE'] >= 15),
            (df['industry_strength_score'] >= 65.0) & (df['SIGNAL_AGE'] >= 6),
            (df['industry_strength_score'] >= 60.0) & (df['SIGNAL_AGE'] <= 5) & (df['strength_acceleration'] > 2.0),
            (df['industry_strength_score'] < 40.0) & (df['strength_acceleration'] <= -5.0)
        ]
        choices_sig = [
            'EXHAUSTED',
            'MATURE',
            'DEVELOPING',
            'NEW',
            'REVERSING'
        ]
        df['SIGNAL_STATE'] = np.select(conds_sig, choices_sig, default='NEUTRAL')

        return df
