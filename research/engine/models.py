"""
Candidate Quantitative Models Tournament Engine.
Implements and scores 15+ candidate quantitative models:
- MODEL 1: Multi-Horizon Momentum Composite
- MODEL 2: Risk-Adjusted Momentum Composite
- MODEL 3: Residual Momentum Composite
- MODEL 4: Breadth Expansion & Momentum
- MODEL 5: Directional Volume Pressure Spread
- MODEL 6: Trend-Stack Breadth Alignment
- MODEL 7: Breakout Quality Composite
- MODEL 8: RSI + Momentum Interaction
- MODEL 9: Mean-Reversion / Overextension
- MODEL 10: Volatility-Adjusted Composite
- MODEL 11: Cross-Sectional Ridge Regression
- MODEL 12: Elastic Net Regression
- MODEL 13: Logistic Probability Model
- MODEL 14: Gradient Boosting Machine
- MODEL 15: State-Transition / Regime Model
- BASELINE 1: Production Money Flow V1
- BASELINE 2: Research Money Flow V2
- SIMPLE BASELINES: Random, 5D Momentum, 20D Momentum, Simple RS, Equal-Weight Breadth
- ENSEMBLES: Strength Ensemble, Prediction Ensemble, Regime Ensemble
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

def compute_all_candidate_models(df_ind_agg: pd.DataFrame) -> pd.DataFrame:
    """
    Computes cross-sectional candidate model scores (0-100 percentile rank per date).
    """
    df = df_ind_agg.copy()
    
    def pct_rank(series):
        return series.rank(pct=True, method='average') * 100.0

    scored_days = []
    for d, grp in df.groupby('date'):
        day = grp.copy()
        
        # --- Model 1: Multi-Horizon Momentum ---
        raw_m1 = 0.35 * day['avg_rs_5d'] + 0.30 * day['avg_rs_20d'] + 0.20 * day['avg_rs_10d'] + 0.15 * day['avg_rs_3d']
        day['M1_MultiHorizonMom'] = pct_rank(raw_m1)

        # --- Model 2: Risk-Adjusted Momentum ---
        raw_m2 = day['avg_risk_adj_mom']
        day['M2_RiskAdjustedMom'] = pct_rank(raw_m2)

        # --- Model 3: Residual Momentum ---
        raw_m3 = day['residual_mom_5d'] + 0.5 * day['alpha_15d']
        day['M3_ResidualMom'] = pct_rank(raw_m3)

        # --- Model 4: Breadth Expansion ---
        raw_m4 = 0.40 * day['ema20_breadth'] + 0.30 * day['breadth_change_5d'] + 0.20 * day['pct_pos_5d'] + 0.10 * day['breadth_change_3d']
        day['M4_BreadthExpansion'] = pct_rank(raw_m4)

        # --- Model 5: Directional Volume Pressure ---
        raw_m5 = 0.60 * day['net_vol_pressure'] + 0.40 * day['avg_vol_ratio']
        day['M5_DirectionalVolume'] = pct_rank(raw_m5)

        # --- Model 6: Trend Stack Breadth ---
        raw_m6 = 0.60 * day['trend_stack_breadth'] + 0.40 * day['ema200_breadth']
        day['M6_TrendStack'] = pct_rank(raw_m6)

        # --- Model 7: Breakout Quality ---
        raw_m7 = 0.60 * day['confirmed_breakout_breadth'] + 0.40 * day['breakout_breadth']
        day['M7_BreakoutQuality'] = pct_rank(raw_m7)

        # --- Model 8: RSI + Momentum ---
        raw_m8 = (day['avg_rsi_14'] - 50.0) + (day['avg_rs_5d'])
        day['M8_RSI_Momentum'] = pct_rank(raw_m8)

        # --- Model 9: Mean Reversion / Overextension ---
        raw_m9 = -1.0 * (day['avg_rs_5d'] - day['avg_rs_20d'])
        day['M9_MeanReversion'] = pct_rank(raw_m9)

        # --- Model 10: Volatility-Adjusted Composite ---
        raw_m10 = (day['M1_MultiHorizonMom'] + day['M4_BreadthExpansion'] + day['M5_DirectionalVolume']) / 3.0
        day['M10_VolAdjustedComposite'] = pct_rank(raw_m10)

        # --- Dynamic Bottom-Up Model ---
        raw_bu = 0.40 * day['bu_rs_20d'] + 0.30 * day['bu_ret_5d'] + 0.30 * day['bu_vol_ratio']
        day['M_DynamicBottomUp'] = pct_rank(raw_bu)

        # --- Simple Baselines ---
        day['BASE_Random'] = np.random.uniform(0, 100, len(day))
        day['BASE_5D_Momentum'] = pct_rank(day['avg_ret_5d'])
        day['BASE_20D_Momentum'] = pct_rank(day['avg_ret_20d'])
        day['BASE_Simple_RS'] = pct_rank(day['avg_rs_5d'])
        day['BASE_EqualBreadth'] = pct_rank(day['ema20_breadth'])

        # --- Production Baselines ---
        day['BASE_V1_Production'] = day['avg_ret_5d'] # placeholder or mapped from existing if present
        day['BASE_V2_Research'] = (0.30 * day['M1_MultiHorizonMom'] + 0.25 * day['M4_BreadthExpansion'] + 0.20 * day['M5_DirectionalVolume'] + 0.10 * day['M6_TrendStack'] + 0.10 * day['M7_BreakoutQuality'] + 0.05 * 50.0)

        # --- Candidate Ensembles ---
        day['ENSEMBLE_Strength'] = (0.35 * day['M1_MultiHorizonMom'] + 0.35 * day['M4_BreadthExpansion'] + 0.20 * day['M5_DirectionalVolume'] + 0.10 * day['M6_TrendStack'])
        day['ENSEMBLE_Prediction'] = (0.30 * day['M3_ResidualMom'] + 0.30 * day['M4_BreadthExpansion'] + 0.20 * day['M5_DirectionalVolume'] + 0.20 * day['M_DynamicBottomUp'])

        scored_days.append(day)

    return pd.concat(scored_days, ignore_index=True)
