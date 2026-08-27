"""
Phase 12: Mandatory Industry Breadth & Universe Partition Engine.
Enforces:
1. PRIMARY_UNIVERSE: constituent_count >= 5 (eligible for rankings, top-k selection, and opportunity cards)
2. RESEARCH_ONLY_UNIVERSE: constituent_count < 5 (retained with status=INSUFFICIENT_INDUSTRY_BREADTH, excluded from primary rankings)
3. Reliability Tiers:
   - N < 5: RESEARCH_ONLY
   - N = 5-9: MODERATE_RELIABILITY
   - N = 10-14: HIGH_RELIABILITY
   - N >= 15: VERY_HIGH_RELIABILITY
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any

def partition_industry_universe(
    df_industry_records: pd.DataFrame,
    min_primary_constituents: int = 5
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Partitions the 135-industry dataset into Primary Universe (N >= 5)
    and Research-Only Universe (N < 5).
    """
    df = df_industry_records.copy()

    # Assign Reliability Tiers based on sample breadth
    reliability_tiers = []
    statuses = []

    for _, row in df.iterrows():
        n = int(row.get('constituent_count', row.get('const_count', 1)))
        if n < min_primary_constituents:
            rel = 'RESEARCH_ONLY'
            st = 'INSUFFICIENT_INDUSTRY_BREADTH'
        elif n <= 9:
            rel = 'MODERATE_RELIABILITY'
            st = 'PRIMARY_ELIGIBLE'
        elif n <= 14:
            rel = 'HIGH_RELIABILITY'
            st = 'PRIMARY_ELIGIBLE'
        else:
            rel = 'VERY_HIGH_RELIABILITY'
            st = 'PRIMARY_ELIGIBLE'

        reliability_tiers.append(rel)
        statuses.append(st)

    df['reliability_tier'] = reliability_tiers
    df['breadth_status'] = statuses

    # Primary Universe: N >= 5
    df_primary = df[df['breadth_status'] == 'PRIMARY_ELIGIBLE'].copy().reset_index(drop=True)

    # Research-Only Universe: N < 5
    df_research_only = df[df['breadth_status'] == 'INSUFFICIENT_INDUSTRY_BREADTH'].copy().reset_index(drop=True)

    return df_primary, df_research_only
