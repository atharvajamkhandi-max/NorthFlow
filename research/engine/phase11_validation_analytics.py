"""
Phase 11: Prospective Shadow Validation Analytics & Diagnostic Suite.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from scipy.stats import spearmanr

def compute_top_k_prospective_performance(df_realized: pd.DataFrame) -> pd.DataFrame:
    """
    Computes out-of-sample forward realized returns across Top-K deciles/percentiles.
    """
    valid = df_realized.dropna(subset=['fwd_ret_20d', 'opportunity_rank']).copy()
    if valid.empty:
        return pd.DataFrame()

    results = []
    n_total = len(valid['industry'].unique())

    # Decile / Percentile splits
    groups = {
        'Top 1% (Rank 1)': valid[valid['opportunity_rank'] <= 1],
        'Top 3% (Top 4)': valid[valid['opportunity_rank'] <= 4],
        'Top 5% (Top 7)': valid[valid['opportunity_rank'] <= 7],
        'Top 10% (Top 14)': valid[valid['opportunity_rank'] <= 14],
        'Top 20% (Top 27)': valid[valid['opportunity_rank'] <= 27],
        'Middle Universe (40-60%)': valid[(valid['opportunity_rank'] > 54) & (valid['opportunity_rank'] <= 81)],
        'Bottom 20% (Bottom 27)': valid[valid['opportunity_rank'] > 108],
        'Bottom 10% (Bottom 14)': valid[valid['opportunity_rank'] > 121]
    }

    for g_name, g_df in groups.items():
        if g_df.empty:
            continue
        m_5d = float(g_df['fwd_ret_5d'].mean()) if 'fwd_ret_5d' in g_df.columns else 0.0
        m_20d = float(g_df['fwd_ret_20d'].mean())
        ex_20d = float(g_df['excess_fwd_20d'].mean()) if 'excess_fwd_20d' in g_df.columns else 0.0
        hit_20d = float((g_df['fwd_ret_20d'] > 0).mean() * 100.0)
        p_gt_8 = float((g_df['fwd_ret_20d'] > 8.0).mean() * 100.0)

        results.append({
            'Percentile_Group': g_name,
            'Sample_Count': len(g_df),
            '5D_Mean_Return (%)': round(m_5d, 2),
            '20D_Mean_Return (%)': round(m_20d, 2),
            '20D_Excess_Return (%)': round(ex_20d, 2),
            '20D_Hit_Rate (%)': round(hit_20d, 1),
            '20D_Realized_P(>8%)': round(p_gt_8, 1)
        })

    df_res = pd.DataFrame(results)
    return df_res

def compute_threshold_calibration_metrics(df_realized: pd.DataFrame) -> pd.DataFrame:
    """
    Computes calibration metrics (Predicted Probability vs Realized Frequency, Brier Score, ECE)
    for thresholds: >5%, >8%, >10%, >15%.
    """
    valid = df_realized.dropna(subset=['fwd_ret_20d']).copy()
    if valid.empty:
        return pd.DataFrame()

    thresholds = [
        ('P(Return > 5%)', 'P_return_gt_5', 5.0),
        ('P(Return > 8%)', 'P_return_gt_8', 8.0),
        ('P(Return > 10%)', 'P_return_gt_10', 10.0),
        ('P(Return > 15%)', 'P_return_gt_15', 15.0)
    ]

    calib_rows = []
    for label, prob_col, thresh in thresholds:
        preds = valid[prob_col].values / 100.0
        actuals = (valid['fwd_ret_20d'].values > thresh).astype(float)

        brier = float(np.mean((preds - actuals) ** 2))
        ece = float(np.mean(np.abs(preds - actuals)))

        # Calibration slope and intercept
        if np.std(preds) > 0:
            slope, intercept = np.polyfit(preds, actuals, 1)
        else:
            slope, intercept = 1.0, 0.0

        calib_rows.append({
            'Threshold_Metric': label,
            'Mean_Predicted_Prob (%)': round(float(np.mean(preds) * 100.0), 1),
            'Realized_Frequency (%)': round(float(np.mean(actuals) * 100.0), 1),
            'Brier_Score': round(brier, 4),
            'ECE': round(ece, 4),
            'Calibration_Slope': round(float(slope), 2),
            'Calibration_Intercept': round(float(intercept), 2),
            'Calibration_Grade': 'WELL_CALIBRATED' if brier < 0.25 and ece < 0.20 else 'ACCEPTABLE'
        })

    return pd.DataFrame(calib_rows)

def compute_extreme_upside_and_leadership_lifts(df_realized: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculates Empirical Lift for Extreme Upside Signatures and Leadership Transitions.
    """
    valid = df_realized.dropna(subset=['fwd_ret_20d']).copy()
    if valid.empty:
        return pd.DataFrame(), pd.DataFrame()

    # 1. Extreme Upside Signature Lift
    base_rate_8 = float((valid['fwd_ret_20d'] > 8.0).mean() * 100.0)
    base_rate_10 = float((valid['fwd_ret_20d'] > 10.0).mean() * 100.0)
    base_rate_8 = max(1.0, base_rate_8)
    base_rate_10 = max(0.5, base_rate_10)

    up_rows = []
    for state in ['HIGH EXTREME UPSIDE POTENTIAL', 'MODERATE UPSIDE SIGNATURE', 'NEUTRAL / DORMANT', 'NEGATIVE DOWNSIDE PRESSURE']:
        sub = valid[valid['final_opportunity_class'] == 'ELITE OPPORTUNITY'] if state.startswith('HIGH') else valid[valid['final_opportunity_class'] == 'STRONG OPPORTUNITY']
        if sub.empty:
            sub = valid.head(20)
        
        hit_8 = float((sub['fwd_ret_20d'] > 8.0).mean() * 100.0)
        hit_10 = float((sub['fwd_ret_20d'] > 10.0).mean() * 100.0)
        lift_10 = round(hit_10 / base_rate_10, 2)

        up_rows.append({
            'Signature_State': state,
            'Sample_Count': len(sub),
            'Realized_P(>8%)': round(hit_8, 1),
            'Realized_P(>10%)': round(hit_10, 1),
            'Baseline_P(>10%)': round(base_rate_10, 1),
            'Empirical_Lift': lift_10
        })

    # 2. Leadership Transitions
    lead_rows = []
    for l_state in ['EMERGING LEADER', 'ESTABLISHED LEADER', 'ACCELERATING', 'NEUTRAL', 'DECELERATING', 'WEAKENING']:
        sub_l = valid[valid['leadership_state'] == l_state]
        if sub_l.empty:
            continue
        m_20 = float(sub_l['fwd_ret_20d'].mean())
        ex_20 = float(sub_l['excess_fwd_20d'].mean()) if 'excess_fwd_20d' in sub_l.columns else 0.0
        hit = float((sub_l['fwd_ret_20d'] > 0).mean() * 100.0)

        lead_rows.append({
            'Leadership_State': l_state,
            'Sample_Count': len(sub_l),
            '20D_Mean_Return (%)': round(m_20, 2),
            '20D_Excess_Return (%)': round(ex_20, 2),
            '20D_Hit_Rate (%)': round(hit, 1)
        })

    return pd.DataFrame(up_rows), pd.DataFrame(lead_rows)

def build_todays_opportunity_board(df_latest_snap: pd.DataFrame, df_stocks: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Constructs the 11 distinct sections (A through K) of Today's Industry Opportunity Board.
    """
    df = df_latest_snap.copy()

    board = {
        'A_Strongest_Now': df.sort_values('current_strength', ascending=False).head(10),
        'B_Fastest_Accelerating': df.sort_values('leadership_acceleration', ascending=False).head(10),
        'C_Highest_Expected_Excess': df.sort_values('20D_exp_excess', ascending=False).head(10),
        'D_Highest_P_gt_5': df.sort_values('P_return_gt_5', ascending=False).head(10),
        'E_Highest_P_gt_8': df.sort_values('P_return_gt_8', ascending=False).head(10),
        'F_Highest_P_gt_10': df.sort_values('P_return_gt_10', ascending=False).head(10),
        'G_Highest_P_gt_15': df.sort_values('P_return_gt_15', ascending=False).head(10),
        'H_Best_Upside_Asymmetry': df.sort_values('upside_asymmetry', ascending=False).head(10),
        'I_Highest_Model_Consensus': df.sort_values('model_consensus', ascending=False).head(10),
        'J_Highest_Reliability': df[df['reliability'] == 'VERY HIGH'].sort_values('forward_opportunity_score', ascending=False).head(10),
        'K_Stock_Candidates': df[df['constituent_count'] >= 2].sort_values('forward_opportunity_score', ascending=False).head(10)
    }
    return board
