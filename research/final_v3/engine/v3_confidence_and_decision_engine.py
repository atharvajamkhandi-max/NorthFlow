"""
Final V3 Production Research Independent Confidence & Decision Engine.
Constructs:
1. CONFIDENCE_SCORE (0-100): Decoupled from Current Strength, incorporating Regime reliability,
   Breadth confirmation, Signal maturity, Dispersion, and Data quality.
2. Explicit Rule-Based FINAL_ACTION: STRONG BUY, BUY, WATCH, NEUTRAL, REDUCE, AVOID.
3. Top Positive Drivers & Top Negative Factors Explainability.
"""

import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

class V3ConfidenceAndDecisionEngine:
    @staticmethod
    def compute_confidence_and_decision(df_ind: pd.DataFrame) -> pd.DataFrame:
        print("Computing Independent Confidence Scores and Explicit Rule-Based Actions...")
        df = df_ind.copy()

        # 1. Independent Confidence Score (0-100)
        # Component A: Regime Reliability (0-100)
        reg_rel = (df['REGIME_CONFIDENCE'].fillna(0.70) * 100.0)
        # Component B: Breadth Confirmation (0-100)
        breadth_conf = df['BREADTH_50'].fillna(50.0)
        # Component C: Sample Breadth / Constituent Count (0-100)
        size_conf = (df['constituent_count'].clip(5, 30) / 30.0 * 100.0)
        # Component D: Signal Penalty for Exhaustion
        sig_penalty = np.where(df['SIGNAL_STATE'] == 'EXHAUSTED', 40.0, np.where(df['SIGNAL_STATE'] == 'MATURE', 20.0, 0.0))

        df['CONFIDENCE_SCORE'] = (
            0.35 * reg_rel +
            0.30 * breadth_conf +
            0.20 * size_conf +
            0.15 * (100.0 - df['RISK_SCORE'].fillna(30.0)) -
            sig_penalty
        ).clip(15, 95).round(1)

        # 2. Explicit Action Rules (STRONG BUY, BUY, WATCH, NEUTRAL, REDUCE, AVOID)
        conds_action = [
            (df['industry_strength_score'] >= 75.0) & (df['CONFIDENCE_SCORE'] >= 65.0) & (df['SIGNAL_STATE'] != 'EXHAUSTED'),
            (df['industry_strength_score'] >= 65.0) & (df['CONFIDENCE_SCORE'] >= 50.0),
            (df['strength_acceleration'] >= 4.0) & (df['industry_strength_score'] >= 45.0),
            (df['SIGNAL_STATE'] == 'EXHAUSTED') & (df['industry_strength_score'] >= 70.0),
            (df['industry_strength_score'] < 35.0) & (df['strength_acceleration'] <= -3.0),
            (df['industry_strength_score'] < 35.0)
        ]
        choices_action = [
            'STRONG BUY',
            'BUY',
            'WATCH',
            'REDUCE',
            'AVOID',
            'AVOID'
        ]
        df['FINAL_ACTION'] = np.select(conds_action, choices_action, default='NEUTRAL')

        # 3. Explainability Drivers & Risks
        def generate_explainability(row):
            pos_drivers = []
            neg_risks = []

            if row['BREADTH_50'] >= 60:
                pos_drivers.append(f"+Broad Participation ({row['BREADTH_50']:.0f}% > SMA50)")
            else:
                neg_risks.append(f"-Weak Breadth Participation ({row['BREADTH_50']:.0f}% > SMA50)")

            if row['industry_RS_market'] > 0:
                pos_drivers.append(f"+Outperforming Benchmark (+{row['industry_RS_market']:.1f}% 20D RS)")
            else:
                neg_risks.append(f"-Underperforming Benchmark ({row['industry_RS_market']:.1f}% 20D RS)")

            if row['strength_acceleration'] > 2.0:
                pos_drivers.append(f"+Strength Accelerating (+{row['strength_acceleration']:.1f} pts)")
            elif row['strength_acceleration'] < -2.0:
                neg_risks.append(f"-Strength Decelerating ({row['strength_acceleration']:.1f} pts)")

            if row['ACCUMULATION_STATE'] == 'ACCUMULATION':
                pos_drivers.append("+Observable Accumulation Pressure")

            if row['SIGNAL_STATE'] == 'EXHAUSTED':
                neg_risks.append("-Signal Becoming Exhausted (Age >= 20)")

            return "; ".join(pos_drivers[:3]), "; ".join(neg_risks[:2])

        exp_data = [generate_explainability(r) for _, r in df.iterrows()]
        df['TOP_POSITIVE_DRIVERS'] = [d[0] for d in exp_data]
        df['TOP_NEGATIVE_FACTORS'] = [d[1] for d in exp_data]

        return df
