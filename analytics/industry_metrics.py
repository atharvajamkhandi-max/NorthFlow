"""
Industry Aggregation and Breadth Engine.
Aggregates constituent stock metrics into granular industry/basic-industry indicators.
Computes both mean and median returns, moving average breadths, breakout breadth,
and identifies low-sample industries.
"""

import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

from database.db import Database
from config.settings import MIN_STOCKS_FOR_RANKING

logger = logging.getLogger(__name__)


class IndustryMetricsCalculator:
    """
    Computes industry-level aggregations and breadth metrics across all trading dates.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    def calculate_all_industry_metrics(self, target_date: Optional[str] = None) -> int:
        """
        Aggregates stock metrics by basic_industry for all dates or target_date.
        Stores aggregated metrics into industry_metrics table.
        """
        logger.info(f"Aggregating industry metrics (target_date={target_date})...")

        # Load stock metrics with prices and stock metadata
        with self.db.get_connection() as conn:
            where_sql = "WHERE sm.date = ?" if target_date else ""
            params = [target_date] if target_date else []
            query = f"""
            SELECT sm.*, dp.delivery_percentage, s.industry, s.basic_industry
            FROM stock_metrics sm
            JOIN stocks s ON sm.symbol = s.symbol
            LEFT JOIN daily_prices dp ON sm.date = dp.date AND sm.symbol = dp.symbol
            {where_sql}
            ORDER BY sm.date ASC, s.basic_industry ASC;
            """
            df = pd.read_sql_query(query, conn, params=params)

        if df.empty:
            logger.warning("No stock metrics available for industry aggregation.")
            return 0

        # Filter out invalid or UNKNOWN basic industries if needed, but keep track of UNKNOWN
        records = []
        for (date_val, basic_ind), group in df.groupby(['date', 'basic_industry']):
            if not basic_ind or str(basic_ind).strip() == "":
                continue

            stock_count = len(group)
            industry_broad = group['industry'].iloc[0] if 'industry' in group.columns else "UNKNOWN"
            is_low_sample = 1 if stock_count < MIN_STOCKS_FOR_RANKING else 0

            # Returns: Mean and Median
            avg_ret_1d = float(group['return_1d'].mean()) if pd.notnull(group['return_1d'].mean()) else 0.0
            med_ret_1d = float(group['return_1d'].median()) if pd.notnull(group['return_1d'].median()) else 0.0

            avg_ret_5d = float(group['return_5d'].mean()) if pd.notnull(group['return_5d'].mean()) else 0.0
            med_ret_5d = float(group['return_5d'].median()) if pd.notnull(group['return_5d'].median()) else 0.0

            avg_ret_20d = float(group['return_20d'].mean()) if pd.notnull(group['return_20d'].mean()) else 0.0
            med_ret_20d = float(group['return_20d'].median()) if pd.notnull(group['return_20d'].median()) else 0.0

            # Relative Strength
            rs_5d = float(group['rs_5d'].mean()) if pd.notnull(group['rs_5d'].mean()) else 0.0
            rs_20d = float(group['rs_20d'].mean()) if pd.notnull(group['rs_20d'].mean()) else 0.0

            # Volume Ratio
            avg_vol_ratio = float(group['volume_ratio'].mean()) if pd.notnull(group['volume_ratio'].mean()) else 1.0

            # Breadth Indicators (%)
            pos_breadth = float((group['return_1d'] > 0).mean() * 100.0)
            ema20_b = float((group['above_20ema'] == 1).mean() * 100.0)
            ema50_b = float((group['above_50ema'] == 1).mean() * 100.0)
            ema200_b = float((group['above_200ema'] == 1).mean() * 100.0)

            # Breakout Breadth
            breakout_cnt = int((group['is_breakout_20d'] == 1).sum())
            breakout_pct = float((breakout_cnt / stock_count) * 100.0) if stock_count > 0 else 0.0

            # Delivery Strength
            deliv_series = group['delivery_percentage'].dropna()
            avg_deliv_pct = float(deliv_series.mean()) if not deliv_series.empty else None

            records.append({
                'date': date_val,
                'industry': industry_broad,
                'basic_industry': basic_ind,
                'stock_count': stock_count,
                'avg_return_1d': avg_ret_1d,
                'median_return_1d': med_ret_1d,
                'avg_return_5d': avg_ret_5d,
                'median_return_5d': med_ret_5d,
                'avg_return_20d': avg_ret_20d,
                'median_return_20d': med_ret_20d,
                'industry_rs_5d': rs_5d,
                'industry_rs_20d': rs_20d,
                'avg_volume_ratio': avg_vol_ratio,
                'positive_breadth': pos_breadth,
                'ema20_breadth': ema20_b,
                'ema50_breadth': ema50_b,
                'ema200_breadth': ema200_b,
                'breakout_count': breakout_cnt,
                'breakout_percentage': breakout_pct,
                'avg_delivery_percentage': avg_deliv_pct,
                'score_today': 0.0,
                'score_1d_ago': 0.0,
                'score_3d_ago': 0.0,
                'score_5d_ago': 0.0,
                'score_change_1d': 0.0,
                'score_change_3d': 0.0,
                'score_change_5d': 0.0,
                'status': 'WEAK',
                'is_low_sample': is_low_sample
            })

        df_ind = pd.DataFrame(records)
        inserted = self.db.insert_or_replace_df("industry_metrics", df_ind)
        logger.info(f"Aggregated and saved {inserted} industry metric records into industry_metrics table.")
        return inserted
