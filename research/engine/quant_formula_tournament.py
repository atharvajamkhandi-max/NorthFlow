"""
Quantitative Research Module: Mathematical Formula Discovery, Ablation, and Testing Lab.
Tests 8 candidate mathematical formulas against the Champion Baseline (Existing_Deterministic_V1).
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy.stats import spearmanr, pearsonr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

class QuantFormulaTournament:
    @staticmethod
    def run_formula_tournament(df_targets: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        print("\n--- [Formula Tournament] Testing 8 Mathematical Formulas vs Champion Baseline ---")
        df = df_targets[df_targets['is_primary_eligible'] == 1].dropna(subset=['future_excess_return_20D']).copy()

        # F0: Baseline Existing Champion
        df['F0_Baseline_Existing'] = (df['industry_strength_score'].fillna(50.0) - 50.0) * 0.15
        
        # F1: Momentum Acceleration
        df['F1_Mom_Acceleration'] = df.groupby('basic_industry')['industry_return_5'].diff(5).fillna(0.0)
        
        # F2: Relative Strength Acceleration
        df['F2_RS_Acceleration'] = df.groupby('basic_industry')['industry_RS_market'].diff(5).fillna(0.0)
        
        # F3: Breadth Acceleration
        df['F3_Breadth_Acceleration'] = df['breadth_acceleration'].fillna(0.0)
        
        # F4: Volume Confirmation
        df['F4_Volume_Confirmation'] = (np.sign(df['industry_return_5'].fillna(0.0)) * df['volume_strength'].fillna(1.0).clip(0, 3) * df['industry_RS_market'].fillna(0.0)).clip(-30, 30)
        
        # F5: Trend Coherence
        df['F5_Trend_Coherence'] = (df['trend_stack_breadth'].fillna(50.0) / 100.0) * df['breadth_50'].fillna(50.0)
        
        # F6: Risk-Adjusted Momentum
        df['F6_Risk_Adjusted_Mom'] = (df['industry_return_20'].fillna(0.0) / np.maximum(5.0, df['volatility'].fillna(15.0))).clip(-10, 10)
        
        # F7: Pressure Persistence
        df['F7_Pressure_Persistence'] = df.groupby('basic_industry')['ACCUMULATION_PRESSURE_SCORE'].transform(lambda x: x.rolling(5, min_periods=1).mean()).fillna(50.0)
        
        # F8: Leadership Acceleration
        df['F8_Leadership_Acceleration'] = df['strength_acceleration'].fillna(0.0)

        # F9: Enhanced Deterministic Hybrid
        df['F9_HYBRID_CHALLENGER'] = (
            0.50 * df['F0_Baseline_Existing'] +
            0.20 * (df['F3_Breadth_Acceleration'].clip(-15, 15) * 0.2) +
            0.20 * (df['F2_RS_Acceleration'].clip(-15, 15) * 0.2) +
            0.10 * (df['F5_Trend_Coherence'] * 0.05)
        )

        formulas = [
            ("F0_Baseline_Existing", "Existing Champion Deterministic Score Mapping", 1),
            ("F1_Mom_Acceleration", "Momentum Acceleration: M_20(t) - M_20(t-5)", 2),
            ("F2_RS_Acceleration", "Relative Strength Acceleration: RS_20(t) - RS_20(t-5)", 2),
            ("F3_Breadth_Acceleration", "Breadth Acceleration: B_50(t) - B_50(t-5)", 2),
            ("F4_Volume_Confirmation", "Observable Volume Confirmation Interaction", 3),
            ("F5_Trend_Coherence", "Trend Coherence & Breadth Convergence", 2),
            ("F6_Risk_Adjusted_Mom", "Risk-Adjusted Momentum: Return / Volatility", 2),
            ("F7_Pressure_Persistence", "Observable Accumulation Pressure 5D Persistence", 2),
            ("F8_Leadership_Acceleration", "Industry Leadership Acceleration Derivative", 2),
            ("F9_HYBRID_CHALLENGER", "Enhanced Deterministic Hybrid (Champion + Acceleration)", 4)
        ]

        y_true = df['future_excess_return_20D'].values
        mask_base = df['F0_Baseline_Existing'].notnull() & df['future_excess_return_20D'].notnull()
        base_ric, _ = spearmanr(df.loc[mask_base, 'F0_Baseline_Existing'], df.loc[mask_base, 'future_excess_return_20D'])
        
        top_base = df.loc[df['F0_Baseline_Existing'] >= df['F0_Baseline_Existing'].quantile(0.9), 'future_excess_return_20D'].mean()
        bot_base = df.loc[df['F0_Baseline_Existing'] <= df['F0_Baseline_Existing'].quantile(0.1), 'future_excess_return_20D'].mean()
        base_spread = float(top_base - bot_base)
        base_sharpe = base_spread / max(1.0, float(np.std(y_true)))

        tourney_records = []
        for col, desc, comp in formulas:
            mask = df[col].notnull() & df['future_excess_return_20D'].notnull()
            sig = df.loc[mask, col].values
            acts = df.loc[mask, 'future_excess_return_20D'].values
            
            ric, _ = spearmanr(sig, acts) if len(sig) > 10 else (0.0, 1.0)
            ic, _ = pearsonr(sig, acts) if len(sig) > 10 else (0.0, 1.0)
            
            q90 = np.percentile(sig, 90)
            q10 = np.percentile(sig, 10)
            top_q = float(np.mean(acts[sig >= q90])) if len(acts[sig >= q90]) > 0 else 0.0
            bot_q = float(np.mean(acts[sig <= q10])) if len(acts[sig <= q10]) > 0 else 0.0
            spread = top_q - bot_q
            sharpe = spread / max(1.0, float(np.std(acts)))

            delta_ric = ric - base_ric
            delta_spread = spread - base_spread
            delta_sharpe = sharpe - base_sharpe

            comp_score = 10.0 * comp
            net_score = round((ric * 100.0) - (comp * 1.5), 2)

            tourney_records.append({
                "Formula_ID": col,
                "Formula_Description": desc,
                "Complexity_Score": comp_score,
                "Rank_IC": round(ric, 4),
                "IC": round(ic, 4),
                "Decile_Spread": round(spread, 2),
                "Sharpe": round(sharpe, 2),
                "Delta_Rank_IC": round(delta_ric, 4),
                "Delta_Spread": round(delta_spread, 2),
                "Delta_Sharpe": round(delta_sharpe, 2),
                "Net_Alpha_Score": net_score,
                "Status": "CHAMPION" if col == "F0_Baseline_Existing" else ("TOP_CHALLENGER" if delta_ric > 0 else "REJECTED")
            })

        df_tourney = pd.DataFrame(tourney_records).sort_values('Rank_IC', ascending=False).reset_index(drop=True)
        print("\n=== FORMULA TOURNAMENT SCORECARD ===")
        print(df_tourney[['Formula_ID', 'Rank_IC', 'Delta_Rank_IC', 'Decile_Spread', 'Delta_Spread', 'Net_Alpha_Score', 'Status']].to_string(index=False))
        return df_tourney, df
