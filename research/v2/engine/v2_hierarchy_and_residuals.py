"""
Phase V2 Hierarchy Engine & Multi-Level Residualized Targets.
Constructs:
1. Market Engine & 6-State Market Regime
2. Sector Strength & Sector Relative Returns
3. Industry Matrix with Hard Breadth Rule (N >= 5 Primary vs N < 5 Research-Only)
4. Multi-Horizon Forward Targets: ER_market, ER_sector, ER_industry (1D, 5D, 20D, 60D)
5. Hierarchical Residualized Target: epsilon_i = R_i - beta_sec * R_sec - beta_ind * R_ind
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.linear_model import Ridge

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, BASE_DIR)

class V2HierarchyAndResiduals:
    @staticmethod
    def compute_hierarchical_aggregates(df_prices: pd.DataFrame, df_bench: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        print("Computing Market, Sector, and Industry aggregates...")
        
        # 1. Market Aggregates
        mkt_df = df_prices.groupby('date').agg(
            mkt_pct_above_sma50=('price_vs_sma50', lambda x: (x > 0).mean() * 100.0),
            mkt_pct_above_sma20=('price_vs_sma20', lambda x: (x > 0).mean() * 100.0),
            mkt_pct_above_sma200=('price_vs_sma200', lambda x: (x > 0).mean() * 100.0),
            mkt_dispersion_20d=('ret_20d', 'std')
        ).reset_index()

        bench_map = df_bench.set_index('date')['return_20d'].to_dict() if 'return_20d' in df_bench.columns else {}
        mkt_df['bench_ret_20d'] = mkt_df['date'].map(bench_map).fillna(0.0)

        mkt_df['market_strength_score'] = (
            0.35 * mkt_df['mkt_pct_above_sma50'] +
            0.35 * mkt_df['mkt_pct_above_sma20'] +
            0.15 * mkt_df['bench_ret_20d'].clip(-20, 20) * 2.5 + 50.0 * 0.15 +
            0.15 * mkt_df['mkt_pct_above_sma200']
        ).clip(0, 100).round(2)

        conds_regime = [
            (mkt_df['mkt_pct_above_sma50'] >= 65.0) & (mkt_df['bench_ret_20d'] >= 3.0),
            (mkt_df['mkt_pct_above_sma50'] >= 50.0),
            (mkt_df['mkt_dispersion_20d'] >= 25.0),
            (mkt_df['mkt_pct_above_sma50'] < 30.0) & (mkt_df['bench_ret_20d'] <= -3.0),
            (mkt_df['mkt_pct_above_sma50'] < 40.0)
        ]
        choices_regime = ['STRONG_BULL', 'WEAK_BULL', 'HIGH_VOLATILITY', 'STRONG_BEAR', 'WEAK_BEAR']
        mkt_df['market_regime'] = np.select(conds_regime, choices_regime, default='SIDEWAYS')

        # 2. Sector Aggregates
        valid_sec = df_prices[df_prices['industry'].notnull() & (df_prices['industry'] != 'UNKNOWN')].copy()
        sec_df = valid_sec.groupby(['date', 'industry']).agg(
            constituent_count=('symbol', 'count'),
            sector_return_5=('ret_5d', 'mean'),
            sector_return_20=('ret_20d', 'mean'),
            sector_breadth_50=('price_vs_sma50', lambda x: (x > 0).mean() * 100.0)
        ).reset_index()
        sec_df['sector_strength_score'] = sec_df['sector_breadth_50'].clip(0, 100).round(2)

        # 3. Industry Aggregates (N >= 5 Primary Rule)
        valid_ind = df_prices[df_prices['basic_industry'].notnull() & (df_prices['basic_industry'] != 'UNKNOWN')].copy()
        ind_df = valid_ind.groupby(['date', 'basic_industry', 'industry']).agg(
            constituent_count=('symbol', 'count'),
            industry_return_1d_median=('ret_1d', 'median'),
            industry_return_5=('ret_5d', 'mean'),
            industry_return_20=('ret_20d', 'mean'),
            industry_RS_market=('market_rs_20d', 'mean'),
            industry_RS_sector=('sector_rs_20d', 'mean'),
            breadth_50=('price_vs_sma50', lambda x: (x > 0).mean() * 100.0),
            trend_stack_breadth=('trend_stack_score', lambda x: (x >= 80.0).mean() * 100.0),
            positive_momentum_ratio=('momentum_20d', lambda x: (x > 0).mean() * 100.0),
            volume_strength=('rel_vol_20d', 'mean'),
            volatility=('realized_vol_20d', 'mean'),
            dispersion=('ret_20d', lambda x: x.std() if len(x) > 1 else 0.0),
            avg_delivery_pct=('delivery_pct', 'mean')
        ).reset_index()

        ind_df['is_primary_eligible'] = (ind_df['constituent_count'] >= 5).astype(int)
        ind_df['breadth_category'] = np.where(ind_df['constituent_count'] >= 5, 'PRIMARY_QUALIFIED', 'INSUFFICIENT_INDUSTRY_BREADTH')

        # Industry Strength Score (0 to 100)
        ind_df['industry_strength_score'] = (
            0.30 * ind_df['breadth_50'] +
            0.25 * ind_df['industry_RS_market'].clip(-20, 20) * 2.5 + 50.0 * 0.25 +
            0.25 * ind_df['trend_stack_breadth'] +
            0.20 * ind_df['volume_strength'].clip(0, 3) * 33.33
        ).clip(0, 100).round(2)

        ind_df = ind_df.sort_values(['basic_industry', 'date']).reset_index(drop=True)
        ind_df['breadth_prev_5d'] = ind_df.groupby('basic_industry')['breadth_50'].shift(5).fillna(ind_df['breadth_50'])
        ind_df['breadth_acceleration'] = (ind_df['breadth_50'] - ind_df['breadth_prev_5d']).round(2)

        ind_df['strength_prev_5d'] = ind_df.groupby('basic_industry')['industry_strength_score'].shift(5).fillna(ind_df['industry_strength_score'])
        ind_df['strength_acceleration'] = (ind_df['industry_strength_score'] - ind_df['strength_prev_5d']).round(2)

        # Merge Market regime into ind_df
        mkt_map = mkt_df.set_index('date').to_dict('index')
        ind_df['market_strength_score'] = ind_df['date'].map(lambda d: mkt_map.get(d, {}).get('market_strength_score', 50.0))
        ind_df['market_regime'] = ind_df['date'].map(lambda d: mkt_map.get(d, {}).get('market_regime', 'SIDEWAYS'))

        return mkt_df, sec_df, ind_df

    @staticmethod
    def compute_residualized_targets(df_prices: pd.DataFrame, df_bench: pd.DataFrame) -> pd.DataFrame:
        print("Computing multi-horizon targets and cross-sectional residual returns epsilon_i...")
        df = df_prices.copy()
        
        # Benchmark map
        b_dict = df_bench.set_index('date').to_dict('index')
        
        # Sector and Industry means per date
        sec_mean_map = df.groupby(['date', 'industry'])['ret_20d'].mean().to_dict()
        ind_mean_map = df.groupby(['date', 'basic_industry'])['ret_20d'].mean().to_dict()

        # Compute stock forward returns over horizons h in [1, 5, 20, 60]
        grp = df.groupby('symbol')
        for h in [1, 5, 20, 60]:
            df[f'future_return_{h}d'] = grp['ret_1d'].shift(-1).transform(lambda x: x.rolling(h, min_periods=max(1, h//2)).sum().shift(-(h-1))).round(2)
            
            # Benchmark forward return
            df[f'bench_fwd_{h}d'] = df['date'].map(lambda d: b_dict.get(d, {}).get(f'return_{h}d', 0.0)).fillna(0.0)
            
            # Market Excess Target
            df[f'ER_market_{h}d'] = (df[f'future_return_{h}d'] - df[f'bench_fwd_{h}d']).round(2)

        # 20D Sector Excess & Industry Excess Targets
        sec_fwd_20 = df.groupby(['date', 'industry'])[f'future_return_20d'].transform('mean').fillna(0.0)
        ind_fwd_20 = df.groupby(['date', 'basic_industry'])[f'future_return_20d'].transform('mean').fillna(0.0)
        
        df['ER_sector_20d'] = (df['future_return_20d'] - sec_fwd_20).round(2)
        df['ER_industry_20d'] = (df['future_return_20d'] - ind_fwd_20).round(2)

        # Residual Target epsilon_i = R_i - beta_sec * R_sec - beta_ind * R_ind
        # In standardized form, epsilon_i is the Industry-Excess return
        df['residual_target_20d'] = df['ER_industry_20d']

        return df
