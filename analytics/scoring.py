"""
Money Flow Scoring and Stock Leadership Engine.
Calculates cross-sectionally normalized 0-100 Money Flow Scores for industries,
and ranks constituent stocks with an institutional multi-factor Stock Leadership Score within each industry:
Proximity to Highs (25%), 20D RS vs Smallcap 250 (25%), Trend Stack (15%), 5D RS (15%), Turnover Quality (10%), Breakout (10%).
"""

import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

from database.db import Database
from config.settings import SCORE_WEIGHTS, STOCK_LEADERSHIP_WEIGHTS, MIN_STOCKS_FOR_RANKING

logger = logging.getLogger(__name__)


class MoneyFlowScorer:
    """
    Computes normalized Industry Money Flow Scores and constituent Stock Leadership Scores.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    @staticmethod
    def _percentile_rank(series: pd.Series) -> pd.Series:
        """
        Computes robust percentile rank [0.0, 100.0] for a series.
        If all values are identical or series has 1 element, returns 50.0.
        """
        valid = series.dropna()
        if len(valid) <= 1 or valid.nunique() <= 1:
            return pd.Series(50.0, index=series.index)
        
        return series.rank(pct=True, method='average') * 100.0

    def calculate_industry_money_flow_scores(self, target_date: Optional[str] = None) -> int:
        """
        Computes Money Flow Score for all industries on each trading date.
        Updates score_today in industry_metrics table.
        """
        logger.info(f"Calculating Industry Money Flow Scores (target_date={target_date})...")
        
        with self.db.get_connection() as conn:
            where_sql = "WHERE date = ?" if target_date else ""
            params = [target_date] if target_date else []
            query = f"SELECT * FROM industry_metrics {where_sql} ORDER BY date ASC, basic_industry ASC;"
            df_ind = pd.read_sql_query(query, conn, params=params)

        if df_ind.empty:
            logger.warning("No industry metrics found for scoring.")
            return 0

        scored_records = []
        for date_val, group in df_ind.groupby('date'):
            group = group.copy().reset_index(drop=True)
            
            # Cross-sectional percentile ranking
            pct_rs_5d = self._percentile_rank(group['industry_rs_5d'])
            pct_rs_20d = self._percentile_rank(group['industry_rs_20d'])
            pct_breadth = (
                group['ema20_breadth'] * 0.4 +
                group['ema50_breadth'] * 0.3 +
                group['positive_breadth'] * 0.3
            )
            pct_vol = self._percentile_rank(group['avg_volume_ratio'])
            pct_breakout = self._percentile_rank(group['breakout_percentage'])

            # Delivery weight handling
            has_delivery = group['avg_delivery_percentage'].notnull().any() and not (group['avg_delivery_percentage'] == 0).all()
            if has_delivery:
                pct_delivery = self._percentile_rank(group['avg_delivery_percentage'])
                w_deliv = SCORE_WEIGHTS.get("delivery_strength", 5.0)
            else:
                pct_delivery = pd.Series(0.0, index=group.index)
                w_deliv = 0.0

            w_rs5 = SCORE_WEIGHTS.get("rs_5d", 30.0)
            w_rs20 = SCORE_WEIGHTS.get("rs_20d", 20.0)
            w_brd = SCORE_WEIGHTS.get("breadth", 20.0)
            w_vol = SCORE_WEIGHTS.get("volume_expansion", 15.0)
            w_bo = SCORE_WEIGHTS.get("breakout_breadth", 10.0)

            total_weight = w_rs5 + w_rs20 + w_brd + w_vol + w_bo + w_deliv
            
            # Multi-factor score
            raw_score = (
                pct_rs_5d * w_rs5 +
                pct_rs_20d * w_rs20 +
                pct_breadth * w_brd +
                pct_vol * w_vol +
                pct_breakout * w_bo +
                pct_delivery * w_deliv
            ) / total_weight

            group['score_today'] = raw_score.round(1)
            scored_records.append(group)

        df_scored = pd.concat(scored_records, ignore_index=True)
        
        # Filter down to exact industry_metrics table columns
        cols = [
            'date', 'industry', 'basic_industry', 'stock_count',
            'avg_return_1d', 'median_return_1d', 'avg_return_5d', 'median_return_5d',
            'avg_return_20d', 'median_return_20d', 'industry_rs_5d', 'industry_rs_20d',
            'avg_volume_ratio', 'positive_breadth', 'ema20_breadth', 'ema50_breadth',
            'ema200_breadth', 'breakout_count', 'breakout_percentage', 'avg_delivery_percentage',
            'score_today', 'score_1d_ago', 'score_3d_ago', 'score_5d_ago',
            'score_change_1d', 'score_change_3d', 'score_change_5d', 'status', 'is_low_sample'
        ]
        df_save = df_scored[[c for c in cols if c in df_scored.columns]]
        inserted = self.db.insert_or_replace_df("industry_metrics", df_save)
        logger.info(f"Updated Money Flow Scores for {inserted} industry records.")
        return inserted

    def calculate_stock_leadership_scores(self, target_date: Optional[str] = None) -> int:
        """
        Computes the Institutional Multi-Factor Stock Leadership Score within each basic_industry.
        Formula:
          25% Proximity to Highs + 25% 20D RS (vs Smallcap 250) + 15% Trend Stack + 15% 5D RS + 10% Turnover Quality + 10% Breakout
        Updates leadership_score in stock_metrics table.
        """
        logger.info(f"Calculating Institutional Stock Leadership Scores (target_date={target_date})...")

        with self.db.get_connection() as conn:
            where_sql = "WHERE sm.date = ?" if target_date else ""
            params = [target_date] if target_date else []
            query = f"""
            SELECT sm.*, s.basic_industry
            FROM stock_metrics sm
            JOIN stocks s ON sm.symbol = s.symbol
            {where_sql}
            ORDER BY sm.date ASC, s.basic_industry ASC, sm.symbol ASC;
            """
            df_sm = pd.read_sql_query(query, conn, params=params)

        if df_sm.empty:
            logger.warning("No stock metrics found for leadership scoring.")
            return 0

        scored_stocks = []
        for (date_val, basic_ind), group in df_sm.groupby(['date', 'basic_industry']):
            group = group.copy().reset_index(drop=True)
            
            # Intra-industry Factor Percentiles
            pr_prox = self._percentile_rank(group['high_proximity'])
            pr_rs20 = self._percentile_rank(group['rs_20d'])
            pr_stack = self._percentile_rank(group['trend_stack'])
            pr_rs5 = self._percentile_rank(group['rs_5d'])
            pr_t_qual = self._percentile_rank(group['turnover_quality'])
            pr_bo = self._percentile_rank(group['is_breakout_20d'])

            w_prox = STOCK_LEADERSHIP_WEIGHTS.get("near_high", 25.0)
            w_rs20 = STOCK_LEADERSHIP_WEIGHTS.get("rs_20d", 25.0)
            w_stack = STOCK_LEADERSHIP_WEIGHTS.get("trend_stack", 15.0)
            w_rs5 = STOCK_LEADERSHIP_WEIGHTS.get("rs_5d", 15.0)
            w_tqual = STOCK_LEADERSHIP_WEIGHTS.get("turnover_quality", 10.0)
            w_bo = STOCK_LEADERSHIP_WEIGHTS.get("breakout", 10.0)
            
            total_w = w_prox + w_rs20 + w_stack + w_rs5 + w_tqual + w_bo

            lead_score = (
                pr_prox * w_prox +
                pr_rs20 * w_rs20 +
                pr_stack * w_stack +
                pr_rs5 * w_rs5 +
                pr_t_qual * w_tqual +
                pr_bo * w_bo
            ) / total_w

            group['leadership_score'] = lead_score.round(1)
            scored_stocks.append(group)

        df_all = pd.concat(scored_stocks, ignore_index=True)
        
        # Filter down to stock_metrics columns
        cols = [
            'date', 'symbol', 'close', 'return_1d', 'return_5d', 'return_20d',
            'ema20', 'ema50', 'ema200', 'volume', 'avg_volume_20d', 'volume_ratio',
            'turnover', 'avg_turnover_20d', 'turnover_ratio', 'turnover_quality',
            'high_proximity', 'trend_stack',
            'rs_5d', 'rs_20d', 'is_breakout_20d', 'above_20ema', 'above_50ema',
            'above_200ema', 'dist_ema20', 'dist_ema50', 'leadership_score'
        ]
        df_save = df_all[[c for c in cols if c in df_all.columns]]
        inserted = self.db.insert_or_replace_df("stock_metrics", df_save)
        logger.info(f"Updated Stock Leadership Scores for {inserted} stock metric records.")
        return inserted
