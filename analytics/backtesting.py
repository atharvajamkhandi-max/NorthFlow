"""
Money Flow Empirical Research & Forward Performance Evaluator.
Analyzes forward returns across:
- Money Flow V1 vs Money Flow V2 Quintiles (Q1 Top 20% to Q5 Bottom 20%)
- Flow States (EARLY INFLOW, STRONG LEADER, COOLING, DISTRIBUTION, etc.)
- Directional Volume Models (Model A vs Model B vs Model C)
- Confirmation Classes (HIGH vs CONFLICTING vs LOW)

Outputs: Mean return, median return, hit rate, and top-bottom spreads.
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from database.db import Database

logger = logging.getLogger(__name__)


class MoneyFlowBacktester:
    """
    Evaluates cross-sectional forward performance on available historical sessions.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    def run_evaluation(self) -> Dict[str, Any]:
        """
        Runs empirical forward return evaluation on industry_metrics table.
        """
        with self.db.get_connection() as conn:
            df = pd.read_sql_query("""
                SELECT 
                    date,
                    basic_industry,
                    stock_count,
                    score_today as score_v1,
                    score_v2,
                    price_score,
                    breadth_score,
                    volume_score,
                    trend_score,
                    breakout_score,
                    delivery_score,
                    dir_vol_model_a,
                    dir_vol_model_b,
                    dir_vol_model_c,
                    flow_confirmation,
                    flow_state_v2,
                    conflict_flags,
                    fwd_return_5d,
                    fwd_return_10d,
                    fwd_return_20d
                FROM industry_metrics
                WHERE score_v2 IS NOT NULL
                ORDER BY date ASC, basic_industry ASC;
            """, conn)

        if df.empty:
            return {"status": "EMPTY", "message": "No V2 scored records found in database."}

        # Filter to rows with forward returns
        df_eval = df.dropna(subset=['fwd_return_5d']).copy()
        if df_eval.empty:
            return {"status": "INSUFFICIENT_FORWARD_DATA", "message": "Forward return windows require more sessions."}

        # 1. Quintile Analysis for V2
        df_eval['quintile_v2'] = df_eval.groupby('date')['score_v2'].transform(
            lambda x: pd.qcut(x, q=5, labels=['Q5_Bottom', 'Q4', 'Q3', 'Q2', 'Q1_Top'], duplicates='drop')
        )

        q_summary = df_eval.groupby('quintile_v2', observed=False).agg(
            obs_count=('fwd_return_5d', 'count'),
            mean_fwd_5d=('fwd_return_5d', 'mean'),
            median_fwd_5d=('fwd_return_5d', 'median'),
            hit_rate_pos=('fwd_return_5d', lambda x: (x > 0).mean() * 100.0)
        ).reset_index()

        # Top-Bottom Spread
        q1_mean = q_summary[q_summary['quintile_v2'] == 'Q1_Top']['mean_fwd_5d'].values[0] if not q_summary[q_summary['quintile_v2'] == 'Q1_Top'].empty else 0.0
        q5_mean = q_summary[q_summary['quintile_v2'] == 'Q5_Bottom']['mean_fwd_5d'].values[0] if not q_summary[q_summary['quintile_v2'] == 'Q5_Bottom'].empty else 0.0
        spread_5d = q1_mean - q5_mean

        # 2. Performance by Flow State V2
        state_summary = df_eval.groupby('flow_state_v2').agg(
            obs_count=('fwd_return_5d', 'count'),
            mean_fwd_5d=('fwd_return_5d', 'mean'),
            median_fwd_5d=('fwd_return_5d', 'median'),
            hit_rate_pos=('fwd_return_5d', lambda x: (x > 0).mean() * 100.0)
        ).reset_index().sort_values('mean_fwd_5d', ascending=False)

        # 3. Performance by Flow Confirmation Level
        conf_summary = df_eval.groupby('flow_confirmation').agg(
            obs_count=('fwd_return_5d', 'count'),
            mean_fwd_5d=('fwd_return_5d', 'mean'),
            median_fwd_5d=('fwd_return_5d', 'median')
        ).reset_index()

        # 4. Correlation of Directional Volume Models with Forward 5D Return
        corr_a = df_eval['dir_vol_model_a'].corr(df_eval['fwd_return_5d'])
        corr_b = df_eval['dir_vol_model_b'].corr(df_eval['fwd_return_5d'])
        corr_c = df_eval['dir_vol_model_c'].corr(df_eval['fwd_return_5d'])

        return {
            "status": "SUCCESS",
            "total_evaluated_observations": len(df_eval),
            "sessions_evaluated": df_eval['date'].nunique(),
            "quintile_summary": q_summary,
            "q1_q5_spread_5d": round(spread_5d, 2),
            "state_summary": state_summary,
            "confirmation_summary": conf_summary,
            "directional_vol_correlations": {
                "Model_A_UpMinusDownSpread": round(corr_a, 4),
                "Model_B_ReturnWeightedVolume": round(corr_b, 4),
                "Model_C_ReturnWeightedTurnover": round(corr_c, 4)
            }
        }
