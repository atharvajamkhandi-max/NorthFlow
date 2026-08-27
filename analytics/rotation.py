"""
Industry Rotation and Momentum Acceleration Detector.
Tracks historical Money Flow Scores (1D, 3D, 5D ago) and classifies rotation states:
- EMERGING: Rapidly accelerating score, volume expansion, and improving breadth.
- STRENGTHENING: Steady score improvement into leader territory.
- STRONG: Established market leader with high sustained money flow.
- COOLING: Previously strong industry undergoing pullback or momentum loss.
- DISTRIBUTION: Sharp score degradation and capital exit.
- WEAK: Low relative strength and depressed breadth.
"""

import logging
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

from database.db import Database
from config.settings import ROTATION_THRESHOLDS

logger = logging.getLogger(__name__)


class RotationDetector:
    """
    Computes score velocity and categorizes rotation states across all industries.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    def classify_status(self, score_today: float, score_1d: float, score_3d: float, score_5d: float,
                        score_chg_5d: float, vol_ratio: float, breakout_pct: float) -> str:
        """
        Applies configurable decision matrix to determine industry rotation status.
        """
        # 1. Check EMERGING first: early surge from lower levels
        emg_cfg = ROTATION_THRESHOLDS.get("EMERGING", {})
        if (score_today >= emg_cfg.get("min_score", 50.0) and
            score_chg_5d >= emg_cfg.get("min_5d_change", 15.0) and
            vol_ratio >= emg_cfg.get("min_volume_ratio", 1.0)):
            return "EMERGING"

        # 2. Check STRONG: Top tier leader
        str_cfg = ROTATION_THRESHOLDS.get("STRONG", {})
        if (score_today >= str_cfg.get("min_score", 75.0) and
            score_chg_5d >= str_cfg.get("min_5d_change", 0.0)):
            return "STRONG"

        # 3. Check STRENGTHENING
        stren_cfg = ROTATION_THRESHOLDS.get("STRENGTHENING", {})
        if (score_today >= stren_cfg.get("min_score", 60.0) and
            score_today < stren_cfg.get("max_score", 75.0) and
            score_chg_5d >= stren_cfg.get("min_5d_change", 5.0)):
            return "STRENGTHENING"

        # 4. Check COOLING: Was strong, now falling
        cool_cfg = ROTATION_THRESHOLDS.get("COOLING", {})
        if (score_5d >= cool_cfg.get("min_past_score", 65.0) and
            score_chg_5d <= cool_cfg.get("max_5d_change", -10.0)):
            return "COOLING"

        # 5. Check DISTRIBUTION: Heavy selloff / rotation out
        dist_cfg = ROTATION_THRESHOLDS.get("DISTRIBUTION", {})
        if (score_today <= dist_cfg.get("max_score", 55.0) and
            score_chg_5d <= dist_cfg.get("max_5d_change", -15.0)):
            return "DISTRIBUTION"

        # 6. Check WEAK
        weak_cfg = ROTATION_THRESHOLDS.get("WEAK", {})
        if score_today <= weak_cfg.get("max_score", 45.0):
            return "WEAK"

        # Default fallback
        return "NEUTRAL"

    def calculate_rotation_states(self, target_date: Optional[str] = None) -> int:
        """
        Tracks 1D, 3D, 5D score history and assigns rotation state.
        Updates industry_metrics table.
        """
        logger.info(f"Calculating Industry Rotation States (target_date={target_date})...")

        with self.db.get_connection() as conn:
            query = "SELECT * FROM industry_metrics ORDER BY basic_industry ASC, date ASC;"
            df_ind = pd.read_sql_query(query, conn)

        if df_ind.empty:
            logger.warning("No industry metrics found for rotation calculation.")
            return 0

        updated_records = []
        for basic_ind, group in df_ind.groupby('basic_industry'):
            group = group.copy().sort_values('date').reset_index(drop=True)
            
            # Lagged scores
            group['score_1d_ago'] = group['score_today'].shift(1).fillna(group['score_today'])
            group['score_3d_ago'] = group['score_today'].shift(3).fillna(group['score_today'])
            group['score_5d_ago'] = group['score_today'].shift(5).fillna(group['score_today'])

            # Score differentials
            group['score_change_1d'] = (group['score_today'] - group['score_1d_ago']).round(1)
            group['score_change_3d'] = (group['score_today'] - group['score_3d_ago']).round(1)
            group['score_change_5d'] = (group['score_today'] - group['score_5d_ago']).round(1)

            # Classify status
            status_list = []
            for _, row in group.iterrows():
                st = self.classify_status(
                    score_today=row['score_today'],
                    score_1d=row['score_1d_ago'],
                    score_3d=row['score_3d_ago'],
                    score_5d=row['score_5d_ago'],
                    score_chg_5d=row['score_change_5d'],
                    vol_ratio=row.get('avg_volume_ratio', 1.0),
                    breakout_pct=row.get('breakout_percentage', 0.0)
                )
                status_list.append(st)

            group['status'] = status_list
            updated_records.append(group)

        df_final = pd.concat(updated_records, ignore_index=True)
        
        cols = [
            'date', 'industry', 'basic_industry', 'stock_count',
            'avg_return_1d', 'median_return_1d', 'avg_return_5d', 'median_return_5d',
            'avg_return_20d', 'median_return_20d', 'industry_rs_5d', 'industry_rs_20d',
            'avg_volume_ratio', 'positive_breadth', 'ema20_breadth', 'ema50_breadth',
            'ema200_breadth', 'breakout_count', 'breakout_percentage', 'avg_delivery_percentage',
            'score_today', 'score_1d_ago', 'score_3d_ago', 'score_5d_ago',
            'score_change_1d', 'score_change_3d', 'score_change_5d', 'status', 'is_low_sample'
        ]
        
        if target_date:
            df_to_save = df_final[df_final['date'] == target_date][cols]
        else:
            df_to_save = df_final[cols]

        inserted = self.db.insert_or_replace_df("industry_metrics", df_to_save)
        logger.info(f"Updated rotation states for {inserted} industry records.")
        return inserted
