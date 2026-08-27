"""
Phase D & E: Market Engine, Regime Classifier & Industry Breadth Engine.
1. Market Engine: Market return, breadth (% > SMA20, SMA50, SMA200), volume, dispersion.
2. Market Regime: Rule-based 6-state (STRONG_BULL, WEAK_BULL, SIDEWAYS, WEAK_BEAR, STRONG_BEAR, HIGH_VOLATILITY).
3. Sector Engine: Sector momentum, relative return vs market, sector breadth.
4. Industry Breadth & Constituent Participation: Breadth 20/50/200, positive return ratio, participation dispersion.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

class QuantRegimeAndBreadth:
    @staticmethod
    def compute_market_and_regimes(df_prices: pd.DataFrame, df_bench: pd.DataFrame) -> pd.DataFrame:
        print("Computing market breadth and regime states...")
        date_grp = df_prices.groupby('date')
        
        mkt_df = date_grp.agg(
            total_stocks=('symbol', 'count'),
            mkt_ret_1d=('ret_1d', 'mean'),
            mkt_pct_above_sma20=('price_vs_sma20', lambda x: (x > 0).mean() * 100.0),
            mkt_pct_above_sma50=('price_vs_sma50', lambda x: (x > 0).mean() * 100.0),
            mkt_pct_above_sma200=('price_vs_sma200', lambda x: (x > 0).mean() * 100.0),
            mkt_dispersion_20d=('ret_20d', 'std'),
            mkt_median_vol_ratio=('rel_vol_20d', 'median')
        ).reset_index()

        bench_map = df_bench.set_index('date')['return_20d'].to_dict() if 'return_20d' in df_bench.columns else {}
        mkt_df['bench_ret_20d'] = mkt_df['date'].map(bench_map).fillna(0.0)

        # Market Strength Score (0 to 100)
        mkt_df['market_strength_score'] = (
            0.35 * mkt_df['mkt_pct_above_sma50'] +
            0.35 * mkt_df['mkt_pct_above_sma20'] +
            0.15 * mkt_df['bench_ret_20d'].clip(-20, 20) * 2.5 + 50.0 * 0.15 +
            0.15 * mkt_df['mkt_pct_above_sma200']
        ).clip(0, 100).round(2)

        # Rule-based 6-State Market Regime Classification
        conds_regime = [
            (mkt_df['mkt_pct_above_sma50'] >= 65.0) & (mkt_df['bench_ret_20d'] >= 3.0),
            (mkt_df['mkt_pct_above_sma50'] >= 50.0),
            (mkt_df['mkt_dispersion_20d'] >= 25.0),
            (mkt_df['mkt_pct_above_sma50'] < 30.0) & (mkt_df['bench_ret_20d'] <= -3.0),
            (mkt_df['mkt_pct_above_sma50'] < 40.0)
        ]
        choices_regime = ['STRONG_BULL', 'WEAK_BULL', 'HIGH_VOLATILITY', 'STRONG_BEAR', 'WEAK_BEAR']
        mkt_df['market_regime'] = np.select(conds_regime, choices_regime, default='SIDEWAYS')

        return mkt_df

    @staticmethod
    def compute_industry_matrix(df_prices: pd.DataFrame, mkt_df: pd.DataFrame) -> pd.DataFrame:
        print("Computing industry breadth, constituent participation, and dispersion...")
        valid = df_prices[df_prices['basic_industry'].notnull() & (df_prices['basic_industry'] != 'UNKNOWN')].copy()
        
        ind_grp = valid.groupby(['date', 'basic_industry', 'industry'])
        df_ind = ind_grp.agg(
            constituent_count=('symbol', 'count'),
            industry_return_5=('ret_5d', 'mean'),
            industry_return_10=('ret_10d', 'mean'),
            industry_return_20=('ret_20d', 'mean'),
            industry_return_60=('ret_60d', 'mean'),
            industry_return_1d_median=('ret_1d', 'median'),
            industry_RS_market=('market_rs_20d', 'mean'),
            industry_RS_sector=('sector_rs_20d', 'mean'),
            breadth_20=('price_vs_sma20', lambda x: (x > 0).mean() * 100.0),
            breadth_50=('price_vs_sma50', lambda x: (x > 0).mean() * 100.0),
            breadth_200=('price_vs_sma200', lambda x: (x > 0).mean() * 100.0),
            trend_stack_breadth=('trend_stack_score', lambda x: (x >= 80.0).mean() * 100.0),
            positive_return_ratio=('ret_1d', lambda x: (x > 0).mean() * 100.0),
            positive_momentum_ratio=('momentum_20d', lambda x: (x > 0).mean() * 100.0),
            volume_strength=('rel_vol_20d', 'mean'),
            volatility=('realized_vol_20d', 'mean'),
            dispersion=('ret_20d', lambda x: x.std() if len(x) > 1 else 0.0),
            avg_delivery_pct=('delivery_pct', 'mean')
        ).reset_index()

        # Participation Score: Checks if industry strength is broad or concentrated
        # Higher positive_momentum_ratio + lower dispersion = broader participation
        df_ind['participation_score'] = (
            0.60 * df_ind['positive_momentum_ratio'] +
            0.40 * (100.0 - df_ind['dispersion'].clip(0, 50) * 2.0)
        ).clip(0, 100).round(2)

        # Breadth Acceleration
        df_ind = df_ind.sort_values(['basic_industry', 'date']).reset_index(drop=True)
        df_ind['breadth_prev_5d'] = df_ind.groupby('basic_industry')['breadth_50'].shift(5).fillna(df_ind['breadth_50'])
        df_ind['breadth_acceleration'] = (df_ind['breadth_50'] - df_ind['breadth_prev_5d']).round(2)

        # Merge Market info
        mkt_dict = mkt_df.set_index('date')[['market_strength_score', 'market_regime']].to_dict('index')
        df_ind['market_strength_score'] = df_ind['date'].map(lambda d: mkt_dict.get(d, {}).get('market_strength_score', 50.0))
        df_ind['market_regime'] = df_ind['date'].map(lambda d: mkt_dict.get(d, {}).get('market_regime', 'SIDEWAYS'))

        # Industry Strength Score (0 to 100)
        df_ind['industry_strength_score'] = (
            0.25 * df_ind['breadth_50'] +
            0.20 * df_ind['industry_RS_market'].clip(-20, 20) * 2.5 + 50.0 * 0.20 +
            0.20 * df_ind['trend_stack_breadth'] +
            0.20 * df_ind['participation_score'] +
            0.15 * df_ind['volume_strength'].clip(0, 4) * 25.0
        ).clip(0, 100).round(2)

        # Strength Acceleration (Derivative)
        df_ind['strength_prev_5d'] = df_ind.groupby('basic_industry')['industry_strength_score'].shift(5).fillna(df_ind['industry_strength_score'])
        df_ind['strength_acceleration'] = (df_ind['industry_strength_score'] - df_ind['strength_prev_5d']).round(2)

        # Second Derivative (Curvature)
        df_ind['accel_prev_5d'] = df_ind.groupby('basic_industry')['strength_acceleration'].shift(5).fillna(df_ind['strength_acceleration'])
        df_ind['acceleration_change'] = (df_ind['strength_acceleration'] - df_ind['accel_prev_5d']).round(2)

        # Hard Breadth Partition: N >= 5 Primary vs N < 5 Research-Only
        df_ind['is_primary_eligible'] = (df_ind['constituent_count'] >= 5).astype(int)
        df_ind['breadth_category'] = np.where(df_ind['constituent_count'] >= 5, 'PRIMARY_QUALIFIED', 'INSUFFICIENT_INDUSTRY_BREADTH')

        # Quantitative Industry Classification
        conds_class = [
            (df_ind['industry_strength_score'] >= 70.0) & (df_ind['strength_acceleration'] >= 3.0),
            (df_ind['industry_strength_score'] >= 65.0),
            (df_ind['strength_acceleration'] >= 8.0) & (df_ind['industry_strength_score'] >= 45.0),
            (df_ind['industry_strength_score'] < 35.0) & (df_ind['strength_acceleration'] <= -5.0),
            (df_ind['industry_strength_score'] < 35.0),
            (df_ind['strength_acceleration'] <= -8.0)
        ]
        choices_class = [
            'STRONG_LEADER',
            'ESTABLISHED_LEADER',
            'EMERGING_LEADER',
            'DISTRIBUTION',
            'WEAK',
            'FADING'
        ]
        df_ind['quantitative_leadership_state'] = np.select(conds_class, choices_class, default='NEUTRAL')

        return df_ind
