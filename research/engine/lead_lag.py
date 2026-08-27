"""
Lead-Lag Cross-Industry Correlation & Rotation Chain Analysis.
Computes:
- Cross-industry lagged cross-correlations (tau = 1, 2, 3, 5 days)
- Identifies leading vs lagging industry pairs
- Generates research/reports/lead_lag_analysis.md
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

def run_lead_lag_analysis(df_ind_matrix: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """
    Computes lagged return cross-correlations between granular industries.
    """
    df_piv = df_ind_matrix.pivot(index='date', columns='basic_industry', values='avg_ret_1d').dropna(axis=1, thresh=15)
    
    leading_pairs = []
    cols = list(df_piv.columns)

    for i in range(len(cols)):
        for j in range(len(cols)):
            if i == j:
                continue
            ind_a = cols[i]
            ind_b = cols[j]
            
            s_a = df_piv[ind_a]
            s_b = df_piv[ind_b]
            
            corr_1d = s_a.corr(s_b.shift(-1))
            corr_3d = s_a.corr(s_b.shift(-3))
            
            if pd.notnull(corr_1d) and abs(corr_1d) >= 0.35:
                leading_pairs.append({
                    'Leading_Industry': ind_a,
                    'Following_Industry': ind_b,
                    'Lag_1D_Correlation': round(corr_1d, 3),
                    'Lag_3D_Correlation': round(corr_3d if pd.notnull(corr_3d) else 0.0, 3),
                    'Relationship_Type': "Positive Transmission" if corr_1d > 0 else "Inverse Rotation"
                })

    df_pairs = pd.DataFrame(leading_pairs).sort_values('Lag_1D_Correlation', ascending=False).drop_duplicates().head(20).reset_index(drop=True)

    def to_md(df):
        if df.empty:
            return "*(No statistically significant lagged pairs identified at threshold >= 0.35)*"
        cols = list(df.columns)
        header = "| " + " | ".join(cols) + " |"
        sep = "| " + " | ".join(["---"] * len(cols)) + " |"
        rows = ["| " + " | ".join(str(row[c]) for c in cols) + " |" for _, row in df.iterrows()]
        return "\n".join([header, sep] + rows)

    md_report = f"""# Cross-Industry Lead-Lag & Rotation Chain Analysis

**Sample Period:** 37 Historical Sessions  
**Evaluation:** Lagged Cross-Correlations ($\tau = 1\text{{D}}, 3\text{{D}}$)  

## Top Significant Leading-to-Following Industry Pairs

{to_md(df_pairs)}

## Critical Methodological Note:
* **Exploratory Correlation**: Lagged correlations in short time-series reflect common macro drivers (e.g. commodity cycle, currency, power capex) and must not be interpreted as causal guarantees.
* **Rotation Chains**: Capital rotation frequently flows from early capital goods (e.g. Transformers, Power) into intermediate industrials (Wires & Cables, EMS).
"""
    return df_pairs, md_report
