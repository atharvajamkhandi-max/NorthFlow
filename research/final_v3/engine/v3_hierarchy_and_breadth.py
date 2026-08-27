"""
Final V3 Production Research Hierarchy & Multi-Horizon Breadth Engine.
Constructs:
1. Multi-Tiered Bottom-Up Hierarchy: Market -> Sector -> Industry (N >= 5 Primary) -> Stock
2. Multi-Horizon Breadth: BREADTH_20, BREADTH_50, BREADTH_100
3. Decomposable Industry Current Strength Score
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

class V3HierarchyAndBreadth:
    @staticmethod
    def compute_hierarchy_and_breadth(df_prices: pd.DataFrame, df_bench: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        print("Computing Final V3 Hierarchy and Multi-Horizon Breadth (B20, B50, B100)...")

        # 1. Market Level
        mkt_df = df_prices.groupby('date').agg(
            mkt_breadth_20=('price_vs_sma20', lambda x: (x > 0).mean() * 100.0),
            mkt_breadth_50=('price_vs_sma50', lambda x: (x > 0).mean() * 100.0),
            mkt_breadth_200=('price_vs_sma200', lambda x: (x > 0).mean() * 100.0),
            mkt_dispersion=('ret_20d', 'std')
        ).reset_index()

        bench_map = df_bench.set_index('date')['return_20d'].to_dict() if 'return_20d' in df_bench.columns else {}
        mkt_df['bench_ret_20d'] = mkt_df['date'].map(bench_map).fillna(0.0)

        mkt_df['market_strength_score'] = (
            0.35 * mkt_df['mkt_breadth_50'] +
            0.35 * mkt_df['mkt_breadth_20'] +
            0.15 * mkt_df['bench_ret_20d'].clip(-20, 20) * 2.5 + 50.0 * 0.15 +
            0.15 * mkt_df['mkt_breadth_200']
        ).clip(0, 100).round(2)

        # 2. Sector Level
        valid_sec = df_prices[df_prices['industry'].notnull() & (df_prices['industry'] != 'UNKNOWN')].copy()
        sec_df = valid_sec.groupby(['date', 'industry']).agg(
            constituent_count=('symbol', 'count'),
            sector_return_20=('ret_20d', 'mean'),
            sector_breadth_50=('price_vs_sma50', lambda x: (x > 0).mean() * 100.0)
        ).reset_index()
        sec_df['sector_strength_score'] = sec_df['sector_breadth_50'].clip(0, 100).round(2)

        # 3. Industry Level (Hard N >= 5 Breadth Rule)
        valid_ind = df_prices[df_prices['basic_industry'].notnull() & (df_prices['basic_industry'] != 'UNKNOWN')].copy()
        ind_df = valid_ind.groupby(['date', 'basic_industry', 'industry']).agg(
            constituent_count=('symbol', 'count'),
            industry_return_1d_median=('ret_1d', 'median'),
            industry_return_1d=('ret_1d', 'mean'),
            industry_return_5=('ret_5d', 'mean'),
            industry_return_20=('ret_20d', 'mean'),
            industry_RS_market=('market_rs_20d', 'mean'),
            industry_RS_sector=('sector_rs_20d', 'mean'),
            BREADTH_20=('price_vs_sma20', lambda x: (x > 0).mean() * 100.0),
            BREADTH_50=('price_vs_sma50', lambda x: (x > 0).mean() * 100.0),
            BREADTH_100=('price_vs_sma200', lambda x: (x > 0).mean() * 100.0),
            trend_stack_breadth=('trend_stack_score', lambda x: (x >= 80.0).mean() * 100.0),
            positive_momentum_ratio=('momentum_20d', lambda x: (x > 0).mean() * 100.0),
            volume_strength=('rel_vol_20d', 'mean'),
            volatility=('realized_vol_20d', 'mean'),
            dispersion=('ret_20d', lambda x: x.std() if len(x) > 1 else 0.0),
            avg_delivery_pct=('delivery_pct', 'mean')
        ).reset_index()

        ind_df['breadth_50'] = ind_df['BREADTH_50']
        ind_df['is_primary_eligible'] = (ind_df['constituent_count'] >= 5).astype(int)
        ind_df['breadth_category'] = np.where(ind_df['constituent_count'] >= 5, 'PRIMARY_QUALIFIED', 'INSUFFICIENT_INDUSTRY_BREADTH')

        # Decomposable Factor Contributions for Industry Strength Score
        ind_df['contrib_breadth'] = (0.30 * ind_df['BREADTH_50']).round(2)
        ind_df['contrib_rs'] = (0.25 * (ind_df['industry_RS_market'].clip(-20, 20) * 2.5 + 50.0)).round(2)
        ind_df['contrib_trend'] = (0.25 * ind_df['trend_stack_breadth']).round(2)
        ind_df['contrib_volume'] = (0.20 * (ind_df['volume_strength'].clip(0, 3) * 33.33)).round(2)

        # Total Current Strength Score (0-100)
        ind_df['industry_strength_score'] = (
            ind_df['contrib_breadth'] +
            ind_df['contrib_rs'] +
            ind_df['contrib_trend'] +
            ind_df['contrib_volume']
        ).clip(0, 100).round(2)

        ind_df = ind_df.sort_values(['basic_industry', 'date']).reset_index(drop=True)
        ind_df['breadth_prev_5d'] = ind_df.groupby('basic_industry')['BREADTH_50'].shift(5).fillna(ind_df['BREADTH_50'])
        ind_df['breadth_acceleration'] = (ind_df['BREADTH_50'] - ind_df['breadth_prev_5d']).round(2)

        ind_df['strength_prev_5d'] = ind_df.groupby('basic_industry')['industry_strength_score'].shift(5).fillna(ind_df['industry_strength_score'])
        ind_df['strength_acceleration'] = (ind_df['industry_strength_score'] - ind_df['strength_prev_5d']).round(2)

        mkt_map = mkt_df.set_index('date').to_dict('index')
        ind_df['market_strength_score'] = ind_df['date'].map(lambda d: mkt_map.get(d, {}).get('market_strength_score', 50.0))

        return mkt_df, sec_df, ind_df
