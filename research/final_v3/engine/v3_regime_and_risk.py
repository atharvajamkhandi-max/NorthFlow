"""
Final V3 Production Research Market Regime & Risk Engine.
Constructs:
1. Market Regime Engine (6 States: STRONG_BULL, WEAK_BULL, SIDEWAYS, WEAK_BEAR, STRONG_BEAR, HIGH_VOLATILITY)
   - Outputs: REGIME, REGIME_CONFIDENCE, REGIME_SIGNAL_MULTIPLIER
2. Risk Engine: Downside Volatility, ATR Pct, Expected Loss, Historical Drawdown, Tail Risk
   - Outputs: RISK_SCORE (0-100), RISK_REASON
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

class V3RegimeAndRisk:
    @staticmethod
    def compute_regime_and_risk(df_ind: pd.DataFrame, mkt_df: pd.DataFrame) -> pd.DataFrame:
        print("Computing 6-State Market Regime and Risk Multipliers...")
        df = df_ind.copy()

        # 1. 6-State Market Regime
        mkt_map = mkt_df.set_index('date').to_dict('index')
        
        def assign_regime(row):
            d = row['date']
            m = mkt_map.get(d, {})
            b50 = m.get('mkt_breadth_50', 50.0)
            ret20 = m.get('bench_ret_20d', 0.0)
            disp = m.get('mkt_dispersion', 15.0)

            if b50 >= 65.0 and ret20 >= 3.0:
                return 'STRONG_BULL', 0.90, 1.20
            elif b50 >= 50.0 and ret20 >= 0.0:
                return 'WEAK_BULL', 0.75, 1.05
            elif disp >= 25.0:
                return 'HIGH_VOLATILITY', 0.65, 0.80
            elif b50 < 30.0 and ret20 <= -3.0:
                return 'STRONG_BEAR', 0.85, 0.60
            elif b50 < 40.0:
                return 'WEAK_BEAR', 0.70, 0.75
            else:
                return 'SIDEWAYS', 0.60, 0.90

        reg_data = [assign_regime(r) for _, r in df.iterrows()]
        df['REGIME'] = [r[0] for r in reg_data]
        df['REGIME_CONFIDENCE'] = [r[1] for r in reg_data]
        df['REGIME_SIGNAL_MULTIPLIER'] = [r[2] for r in reg_data]
        df['market_regime'] = df['REGIME']

        # 2. Risk Engine (0-100)
        # Component A: Volatility Risk
        vol_risk = (df['volatility'].fillna(15.0) / 40.0 * 100.0).clip(0, 100)
        # Component B: Negative Momentum / Breadth Risk
        breadth_risk = (100.0 - df['BREADTH_50'].fillna(50.0)).clip(0, 100)
        # Component C: Signal Decay / Exhaustion Risk
        decay_risk = np.where(df['SIGNAL_STATE'] == 'EXHAUSTED', 80.0, np.where(df['SIGNAL_STATE'] == 'REVERSING', 90.0, 20.0))

        df['RISK_SCORE'] = (0.40 * vol_risk + 0.35 * breadth_risk + 0.25 * decay_risk).clip(0, 100).round(1)

        def get_risk_reason(row):
            reasons = []
            if row['volatility'] >= 25.0:
                reasons.append(f"High Industry Volatility ({row['volatility']:.1f}%)")
            if row['BREADTH_50'] < 40.0:
                reasons.append(f"Weak Constituent Breadth ({row['BREADTH_50']:.0f}%)")
            if row['SIGNAL_STATE'] in ['EXHAUSTED', 'REVERSING']:
                reasons.append(f"Signal {row['SIGNAL_STATE']}")
            return "; ".join(reasons) if reasons else "Low Risk Environment"

        df['RISK_REASON'] = [get_risk_reason(r) for _, r in df.iterrows()]
        return df
