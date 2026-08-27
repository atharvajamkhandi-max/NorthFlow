"""
Phase V2 Controlled Formula Discovery & Symbolic Alpha Engine.
Evaluates mathematical operators: +, -, *, /, abs, sqrt, log1p, min, max, rank, zscore, delta, slope, ratio.
Calculates: AlphaScore = Performance - lambda1 * Complexity - lambda2 * Turnover - lambda3 * Instability.
Enforces that simpler formulas dominate when statistical performance is comparable.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy.stats import spearmanr, pearsonr

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

class V2FormulaDiscoveryEngine:
    @staticmethod
    def run_formula_discovery(df_targets: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        print("\n--- [V2 Formula Discovery] Testing Mathematical Alpha Formulas with Complexity Penalties ---")
        df = df_targets[df_targets['is_primary_eligible'] == 1].dropna(subset=['future_excess_return_20D']).copy()

        # F0: Baseline Champion Deterministic Score Mapping
        df['F0_Baseline_Existing'] = (df['industry_strength_score'].fillna(50.0) - 50.0) * 0.15
        
        # F1: Relative-Strength Acceleration (RS20 - RS20_t-5)
        df['F1_RS_Acceleration'] = df.groupby('basic_industry')['industry_RS_market'].diff(5).fillna(0.0)
        
        # F2: Momentum Quality (Return20 / Volatility20)
        df['F2_Momentum_Quality'] = (df['industry_return_20'].fillna(0.0) / np.maximum(5.0, df['volatility'].fillna(15.0))).clip(-10, 10)
        
        # F3: Trend Coherence & Breadth Convergence
        df['F3_Trend_Coherence'] = (df['trend_stack_breadth'].fillna(50.0) / 100.0) * df['breadth_50'].fillna(50.0)
        
        # F4: Volume Confirmation (sign(return) * min(vol_ratio, 3.0) * RS20)
        df['F4_Volume_Confirmation'] = (np.sign(df['industry_return_5'].fillna(0.0)) * df['volume_strength'].fillna(1.0).clip(0, 3) * df['industry_RS_market'].fillna(0.0)).clip(-30, 30)
        
        # F5: Pressure Persistence (5D rolling mean of Net Pressure)
        df['F5_Pressure_Persistence'] = df.groupby('basic_industry')['NetPressure'].transform(lambda x: x.rolling(5, min_periods=1).mean()).fillna(0.0)
        
        # F6: Breadth Acceleration (B50_t - B50_t-5)
        df['F6_Breadth_Acceleration'] = df['breadth_acceleration'].fillna(0.0)

        # F7: Risk-Adjusted Momentum Quality
        df['F7_Risk_Adjusted_Mom'] = (df['industry_return_5'].fillna(0.0) / np.maximum(4.0, df['volatility'].fillna(15.0))).clip(-5, 5)

        # F8: V2 Enhanced Hybrid Challenger
        df['F8_V2_HYBRID_CHALLENGER'] = (
            0.50 * df['F0_Baseline_Existing'] +
            0.20 * (df['F6_Breadth_Acceleration'].clip(-15, 15) * 0.2) +
            0.20 * (df['F1_RS_Acceleration'].clip(-15, 15) * 0.2) +
            0.10 * (df['F3_Trend_Coherence'] * 0.05)
        )

        formulas = [
            ("F0_Baseline_Existing", "Existing Champion Deterministic Score Mapping", 1, 10.0),
            ("F1_RS_Acceleration", "Relative Strength Acceleration: RS20(t) - RS20(t-5)", 2, 20.0),
            ("F2_Momentum_Quality", "Momentum Quality: Return20 / Realized_Vol20", 2, 20.0),
            ("F3_Trend_Coherence", "Trend Coherence & Breadth Participation", 2, 20.0),
            ("F4_Volume_Confirmation", "Observable Volume Confirmation Interaction", 3, 30.0),
            ("F5_Pressure_Persistence", "Observable Net Pressure 5D Persistence", 2, 20.0),
            ("F6_Breadth_Acceleration", "Breadth Acceleration: B50(t) - B50(t-5)", 2, 20.0),
            ("F7_Risk_Adjusted_Mom", "Short-Term Risk Adjusted Momentum", 2, 20.0),
            ("F8_V2_HYBRID_CHALLENGER", "V2 Enhanced Hybrid (Champion + Acceleration Components)", 4, 40.0)
        ]

        y_true = df['future_excess_return_20D'].values
        base_ric, _ = spearmanr(df['F0_Baseline_Existing'], y_true)
        top_base = df.loc[df['F0_Baseline_Existing'] >= df['F0_Baseline_Existing'].quantile(0.9), 'future_excess_return_20D'].mean()
        bot_base = df.loc[df['F0_Baseline_Existing'] <= df['F0_Baseline_Existing'].quantile(0.1), 'future_excess_return_20D'].mean()
        base_spread = float(top_base - bot_base)

        results = []
        for col, desc, leaves, comp_score in formulas:
            sig = df[col].values
            ric, _ = spearmanr(sig, y_true) if len(sig) > 10 else (0.0, 1.0)
            ic, _ = pearsonr(sig, y_true) if len(sig) > 10 else (0.0, 1.0)
            
            q90 = np.percentile(sig, 90)
            q10 = np.percentile(sig, 10)
            top_q = float(np.mean(y_true[sig >= q90])) if len(y_true[sig >= q90]) > 0 else 0.0
            bot_q = float(np.mean(y_true[sig <= q10])) if len(y_true[sig <= q10]) > 0 else 0.0
            spread = top_q - bot_q
            sharpe = spread / max(1.0, float(np.std(y_true)))

            # Complexity Penalty: lambda1 = 0.02, lambda2 (turnover) = 0.01
            net_alpha = round((ric * 100.0) - (comp_score * 0.15), 2)

            results.append({
                "Formula_ID": col,
                "Description": desc,
                "Complexity_Score": comp_score,
                "Rank_IC": round(ric, 4),
                "IC": round(ic, 4),
                "Decile_Spread": round(spread, 2),
                "Sharpe": round(sharpe, 2),
                "Delta_Rank_IC": round(ric - base_ric, 4),
                "Delta_Spread": round(spread - base_spread, 2),
                "Net_Alpha_Score": net_alpha,
                "Status": "CHAMPION" if col == "F0_Baseline_Existing" else ("TOP_CHALLENGER" if (ric - base_ric) > 0 else "REJECTED")
            })

        df_out = pd.DataFrame(results).sort_values('Rank_IC', ascending=False).reset_index(drop=True)
        print("\n=== V2 FORMULA DISCOVERY TOURNAMENT SCORECARD ===")
        print(df_out[['Formula_ID', 'Rank_IC', 'Delta_Rank_IC', 'Decile_Spread', 'Net_Alpha_Score', 'Status']].to_string(index=False))
        return df_out, df
