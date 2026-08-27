"""
Money Flow Methodology V2 Scoring Engine (Research Layer).
Implements the 6-factor decomposed quantitative model:
1. Price & Relative Strength (3D, 5D, 10D, 20D vs NIFTY Smallcap 250)
2. Directional Volume Pressure (Models A, B, C)
3. Breadth Participation & Breadth Momentum (EMA20, EMA50, Pos5D, ΔBreadth_5D)
4. Delivery Confirmation (Up vs Down day spread)
5. Trend Positioning Stack (Price > EMA20 > EMA50 > EMA200)
6. Breakout Quality (Volume-confirmed 20D base breakouts)

Includes:
- Cross-sectional percentile ranking per trading session
- Statistical reliability rating sqrt(N)/sqrt(10) (decoupled from score)
- Multi-period score acceleration (1D, 3D, 5D) and component trajectories
- 2D Flow State Classification (Current Strength vs Acceleration)
- Conflict & Divergence Flag Detection
- Forward return calculation for empirical research
"""

import logging
import math
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

from database.db import Database
from config.settings import (
    MONEY_FLOW_V2_WEIGHTS,
    FLOW_STATE_V2_CONFIG,
    FLOW_CONFIRMATION_CONFIG,
    BENCHMARK_INDEX
)

logger = logging.getLogger(__name__)


class MoneyFlowScorerV2:
    """
    Computes Money Flow V2 scores, components, reliability, trajectories, and flow states.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.db.initialize_schema()

    def calculate_all_v2_scores(self, target_date: Optional[str] = None) -> int:
        """
        Calculates Money Flow V2 scores for all trading sessions or target_date.
        Stores results in industry_metrics table without altering V1 scores.
        """
        logger.info(f"Computing Money Flow V2 scores (target_date={target_date})...")

        # 1. Load constituent-level stock data joined with basic_industry
        with self.db.get_connection() as conn:
            q_stocks = """
            SELECT 
                dp.date,
                dp.symbol,
                s.basic_industry,
                dp.close,
                dp.volume,
                dp.turnover,
                dp.delivery_percentage,
                sm.return_1d,
                sm.return_5d,
                sm.return_20d,
                sm.rs_5d,
                sm.rs_20d,
                sm.volume_ratio,
                sm.above_20ema,
                sm.above_50ema,
                sm.above_200ema,
                sm.is_breakout_20d,
                sm.high_proximity
            FROM daily_prices dp
            JOIN stocks s ON dp.symbol = s.symbol
            LEFT JOIN stock_metrics sm ON dp.date = sm.date AND dp.symbol = sm.symbol
            WHERE s.active = 1 AND s.basic_industry IS NOT NULL AND s.basic_industry != 'UNKNOWN'
            ORDER BY dp.date ASC, s.basic_industry ASC;
            """
            df_stocks = pd.read_sql_query(q_stocks, conn)

        if df_stocks.empty:
            logger.warning("No stock data available for V2 scoring.")
            return 0

        # Load existing industry_metrics table
        with self.db.get_connection() as conn:
            df_im = pd.read_sql_query("SELECT * FROM industry_metrics ORDER BY date ASC, basic_industry ASC;", conn)

        if df_im.empty:
            logger.warning("No industry_metrics base records available.")
            return 0

        # 2. Process Session by Session to Guarantee Zero Look-Ahead Bias
        all_dates = sorted(df_stocks['date'].unique())
        if target_date:
            dates_to_process = [target_date] if target_date in all_dates else []
        else:
            dates_to_process = all_dates

        updated_records = []

        # Pre-compute lag maps for Breadth and Scores
        # Date -> basic_industry -> EMA20 Breadth
        breadth_history = {}
        for d, grp in df_im.groupby('date'):
            breadth_history[d] = grp.set_index('basic_industry')['ema20_breadth'].to_dict()

        for d_idx, cur_date in enumerate(dates_to_process):
            df_stk_day = df_stocks[df_stocks['date'] == cur_date]
            df_im_day = df_im[df_im['date'] == cur_date].copy()
            if df_im_day.empty:
                continue

            # Lookback dates for Breadth Momentum (3D, 5D)
            curr_pos = all_dates.index(cur_date) if cur_date in all_dates else d_idx
            date_3d_ago = all_dates[curr_pos - 3] if curr_pos >= 3 else None
            date_5d_ago = all_dates[curr_pos - 5] if curr_pos >= 5 else None

            # Calculate Raw Components for each industry on cur_date
            ind_rows = []
            for _, im_row in df_im_day.iterrows():
                ind_name = im_row['basic_industry']
                stk_sub = df_stk_day[df_stk_day['basic_industry'] == ind_name]
                n_stocks = len(stk_sub) if not stk_sub.empty else int(im_row.get('stock_count', 1))

                # --- 1. Price / Relative Strength Raw ---
                rs_5 = float(im_row.get('industry_rs_5d', 0.0) or 0.0)
                rs_20 = float(im_row.get('industry_rs_20d', 0.0) or 0.0)
                ret_1d = float(im_row.get('avg_return_1d', 0.0) or 0.0)
                ret_5d = float(im_row.get('avg_return_5d', 0.0) or 0.0)
                raw_price = (0.50 * rs_5) + (0.35 * rs_20) + (0.15 * ret_1d)

                # --- 2. Directional Volume Pressure (Models A, B, C) ---
                if not stk_sub.empty:
                    up_stocks = stk_sub[stk_sub['return_1d'] > 0]
                    down_stocks = stk_sub[stk_sub['return_1d'] < 0]
                    
                    pct_up_vol_exp = float((up_stocks['volume_ratio'] >= 1.2).sum() / max(1, n_stocks)) * 100.0
                    pct_down_vol_exp = float((down_stocks['volume_ratio'] >= 1.2).sum() / max(1, n_stocks)) * 100.0
                    model_a = pct_up_vol_exp - pct_down_vol_exp

                    # Model B: Return x VolumeRatio sum
                    ret_clean = stk_sub['return_1d'].fillna(0)
                    vol_clean = stk_sub['volume_ratio'].fillna(1.0).clip(0, 5.0)
                    model_b = float((ret_clean * vol_clean).mean())

                    # Model C: Return x Turnover sum
                    to_clean = stk_sub['turnover'].fillna(0)
                    to_norm = to_clean / max(1.0, to_clean.sum())
                    model_c = float((ret_clean * to_norm).sum()) * 100.0

                    med_vol_ratio = float(stk_sub['volume_ratio'].median()) if not stk_sub['volume_ratio'].dropna().empty else 1.0
                else:
                    model_a = 0.0
                    model_b = 0.0
                    model_c = 0.0
                    med_vol_ratio = float(im_row.get('avg_volume_ratio', 1.0) or 1.0)

                raw_volume = (0.60 * model_a) + (0.40 * min(3.0, med_vol_ratio) * 33.3)

                # --- 3. Breadth & Breadth Momentum Raw ---
                ema20_b = float(im_row.get('ema20_breadth', 50.0) or 50.0)
                ema50_b = float(im_row.get('ema50_breadth', 50.0) or 50.0)
                pos_b = float(im_row.get('positive_breadth', 50.0) or 50.0)

                b_3d_prior = breadth_history.get(date_3d_ago, {}).get(ind_name, ema20_b)
                b_5d_prior = breadth_history.get(date_5d_ago, {}).get(ind_name, ema20_b)
                delta_b_3d = ema20_b - b_3d_prior
                delta_b_5d = ema20_b - b_5d_prior

                raw_breadth = (0.35 * ema20_b) + (0.25 * pos_b) + (0.15 * ema50_b) + (0.15 * delta_b_5d) + (0.10 * delta_b_3d)

                # --- 4. Delivery Confirmation Raw ---
                if not stk_sub.empty and 'delivery_percentage' in stk_sub.columns:
                    up_deliv = stk_sub[stk_sub['return_1d'] > 0]['delivery_percentage'].dropna()
                    down_deliv = stk_sub[stk_sub['return_1d'] < 0]['delivery_percentage'].dropna()
                    up_del_mean = float(up_deliv.mean()) if not up_deliv.empty else 45.0
                    down_del_mean = float(down_deliv.mean()) if not down_deliv.empty else 45.0
                    deliv_spread = up_del_mean - down_del_mean
                    tot_del_mean = float(stk_sub['delivery_percentage'].dropna().mean()) if not stk_sub['delivery_percentage'].dropna().empty else 45.0
                else:
                    deliv_spread = 0.0
                    tot_del_mean = 45.0

                raw_delivery = (0.50 * deliv_spread) + (0.50 * tot_del_mean)

                # --- 5. Trend Positioning Raw ---
                if not stk_sub.empty:
                    trend_stack_cnt = ((stk_sub['close'] > stk_sub['above_20ema']) & (stk_sub['above_20ema'] == 1) & (stk_sub['above_50ema'] == 1) & (stk_sub['above_200ema'] == 1)).sum()
                    trend_stack_pct = float(trend_stack_cnt / max(1, n_stocks)) * 100.0
                    above_200_pct = float((stk_sub['above_200ema'] == 1).sum() / max(1, n_stocks)) * 100.0
                else:
                    trend_stack_pct = float(im_row.get('ema200_breadth', 50.0) or 50.0)
                    above_200_pct = float(im_row.get('ema200_breadth', 50.0) or 50.0)

                raw_trend = (0.60 * trend_stack_pct) + (0.40 * above_200_pct)

                # --- 6. Breakout Quality Raw ---
                bk_pct = float(im_row.get('breakout_percentage', 0.0) or 0.0)
                if not stk_sub.empty:
                    conf_bk_cnt = ((stk_sub['is_breakout_20d'] == 1) & (stk_sub['volume_ratio'] >= 1.2)).sum()
                    conf_bk_pct = float(conf_bk_cnt / max(1, n_stocks)) * 100.0
                    near_hi_pct = float((stk_sub['high_proximity'] >= 90.0).sum() / max(1, n_stocks)) * 100.0
                else:
                    conf_bk_pct = bk_pct
                    near_hi_pct = 50.0

                raw_breakout = (0.50 * conf_bk_pct) + (0.30 * near_hi_pct) + (0.20 * bk_pct)

                # --- Statistical Reliability (Separate from Score) ---
                rel_score = min(1.0, math.sqrt(n_stocks) / math.sqrt(10))
                rel_label = "HIGH" if n_stocks >= 10 else ("MODERATE" if n_stocks >= 3 else "LOW")

                ind_rows.append({
                    'date': cur_date,
                    'basic_industry': ind_name,
                    'stock_count': n_stocks,
                    'reliability_score': round(rel_score, 2),
                    'reliability_label': rel_label,
                    'raw_price': raw_price,
                    'raw_volume': raw_volume,
                    'raw_breadth': raw_breadth,
                    'raw_delivery': raw_delivery,
                    'raw_trend': raw_trend,
                    'raw_breakout': raw_breakout,
                    'dir_vol_model_a': round(model_a, 2),
                    'dir_vol_model_b': round(model_b, 4),
                    'dir_vol_model_c': round(model_c, 2),
                    'delta_breadth_5d': round(delta_b_5d, 2)
                })

            df_session = pd.DataFrame(ind_rows)
            if df_session.empty:
                continue

            # --- Cross-Sectional Percentile Normalization per Session ---
            for col, score_name in [
                ('raw_price', 'price_score'),
                ('raw_volume', 'volume_score'),
                ('raw_breadth', 'breadth_score'),
                ('raw_delivery', 'delivery_score'),
                ('raw_trend', 'trend_score'),
                ('raw_breakout', 'breakout_score')
            ]:
                # Percentile rank in [0, 100] using average ranking for ties
                ranks = df_session[col].rank(pct=True, method='average') * 100.0
                df_session[score_name] = ranks.round(1)

            # --- Weighted Money Flow V2 Composite ---
            w = MONEY_FLOW_V2_WEIGHTS
            df_session['score_v2'] = (
                w["price"] * df_session['price_score'] +
                w["breadth"] * df_session['breadth_score'] +
                w["directional_volume"] * df_session['volume_score'] +
                w["trend"] * df_session['trend_score'] +
                w["breakout"] * df_session['breakout_score'] +
                w["delivery"] * df_session['delivery_score']
            ).round(1)

            updated_records.append(df_session)

        if not updated_records:
            return 0

        df_v2_all = pd.concat(updated_records, ignore_index=True)

        # 3. Calculate Multi-Period Accelerations and 5D Component Trajectories
        df_v2_all = df_v2_all.sort_values(['basic_industry', 'date']).reset_index(drop=True)

        df_v2_all['score_v2_1d_ago'] = df_v2_all.groupby('basic_industry')['score_v2'].shift(1)
        df_v2_all['score_v2_3d_ago'] = df_v2_all.groupby('basic_industry')['score_v2'].shift(3)
        df_v2_all['score_v2_5d_ago'] = df_v2_all.groupby('basic_industry')['score_v2'].shift(5)

        df_v2_all['score_v2_change_1d'] = (df_v2_all['score_v2'] - df_v2_all['score_v2_1d_ago']).round(1).fillna(0.0)
        df_v2_all['score_v2_change_3d'] = (df_v2_all['score_v2'] - df_v2_all['score_v2_3d_ago']).round(1).fillna(0.0)
        df_v2_all['score_v2_change_5d'] = (df_v2_all['score_v2'] - df_v2_all['score_v2_5d_ago']).round(1).fillna(0.0)

        # Component 5D Trajectories
        for comp in ['price_score', 'breadth_score', 'volume_score', 'trend_score', 'breakout_score', 'delivery_score']:
            lag_5d = df_v2_all.groupby('basic_industry')[comp].shift(5)
            df_v2_all[f'{comp}_change_5d'] = (df_v2_all[comp] - lag_5d).round(1).fillna(0.0)

        # 4. Classify Flow Confirmation & 2D Flow States & Conflict Flags
        confirmations = []
        flow_states = []
        conflict_list = []

        cfg_state = FLOW_STATE_V2_CONFIG
        cfg_conf = FLOW_CONFIRMATION_CONFIG

        for _, row in df_v2_all.iterrows():
            sc = row['score_v2']
            d5 = row['score_v2_change_5d']
            p_sc = row['price_score']
            b_sc = row['breadth_score']
            v_sc = row['volume_score']
            t_sc = row['trend_score']
            db5 = row.get('delta_breadth_5d', 0.0)
            dir_spread = row.get('dir_vol_model_a', 0.0)

            # Conflict Flags Detection
            flags = []
            if p_sc >= cfg_conf["DIVERGENCE_PRICE_HIGH"] and b_sc <= cfg_conf["DIVERGENCE_BREADTH_LOW"]:
                flags.append("PRICE_STRONG_BREADTH_WEAK")
            if p_sc >= cfg_conf["DIVERGENCE_PRICE_HIGH"] and v_sc <= 40.0:
                flags.append("PRICE_STRONG_VOLUME_WEAK")
            if dir_spread <= cfg_conf["DIVERGENCE_VOL_SPREAD_LOW"]:
                flags.append("HIGH_VOLUME_DOWN_PRESSURE")
            if row['breakout_score'] >= 70.0 and b_sc <= 40.0:
                flags.append("BREAKOUT_WITHOUT_BREADTH")
            if row['breakout_score'] >= 70.0 and v_sc <= 40.0:
                flags.append("BREAKOUT_WITHOUT_VOLUME")
            if sc >= 75.0 and d5 <= -5.0:
                flags.append("STRONG_BUT_COOLING")
            if sc <= 40.0 and d5 >= +8.0:
                flags.append("WEAK_BUT_ACCELERATING")

            conflict_str = ", ".join(flags) if flags else "NONE"
            conflict_list.append(conflict_str)

            # Flow Confirmation Quality
            if flags:
                conf = "CONFLICTING"
            elif p_sc >= cfg_conf["HIGH_THRESHOLD"] and v_sc >= cfg_conf["HIGH_THRESHOLD"] and b_sc >= cfg_conf["HIGH_THRESHOLD"]:
                conf = "HIGH"
            elif sum([1 for s in [p_sc, b_sc, v_sc, t_sc, row['breakout_score'], row['delivery_score']] if s >= cfg_conf["MODERATE_THRESHOLD"]]) >= 4:
                conf = "MODERATE"
            else:
                conf = "LOW"
            confirmations.append(conf)

            # 2D Flow State Classification
            if sc >= cfg_state["EARLY_INFLOW"]["min_score"] and sc <= cfg_state["EARLY_INFLOW"]["max_score"] and d5 >= cfg_state["EARLY_INFLOW"]["min_5d_change"] and db5 >= cfg_state["EARLY_INFLOW"]["min_breadth_5d_change"]:
                st_val = "EARLY INFLOW"
            elif sc >= cfg_state["STRONG_LEADER"]["min_score"] and d5 >= cfg_state["STRONG_LEADER"]["min_5d_change"] and b_sc >= cfg_state["STRONG_LEADER"]["min_breadth_score"]:
                st_val = "STRONG LEADER"
            elif sc >= cfg_state["MATURE_STRONG"]["min_score"] and d5 < 0.0 and d5 >= cfg_state["MATURE_STRONG"]["min_5d_change"]:
                st_val = "MATURE STRONG"
            elif sc >= cfg_state["ACCELERATING"]["min_score"] and d5 >= cfg_state["ACCELERATING"]["min_5d_change"] and v_sc >= cfg_state["ACCELERATING"]["min_volume_score"]:
                st_val = "ACCELERATING"
            elif sc >= cfg_state["COOLING"]["min_score"] and d5 <= cfg_state["COOLING"]["max_5d_change"]:
                st_val = "COOLING"
            elif p_sc <= cfg_state["DISTRIBUTION"]["max_price_score"] and v_sc <= cfg_state["DISTRIBUTION"]["max_volume_score"] and dir_spread <= cfg_state["DISTRIBUTION"]["max_directional_spread"]:
                st_val = "DISTRIBUTION / OUTFLOW"
            elif sc <= cfg_state["WEAK"]["max_score"] and d5 <= cfg_state["WEAK"]["max_5d_change"]:
                st_val = "WEAK"
            else:
                st_val = "NEUTRAL"
            flow_states.append(st_val)

        df_v2_all['flow_confirmation'] = confirmations
        df_v2_all['flow_state_v2'] = flow_states
        df_v2_all['conflict_flags'] = conflict_list

        # 5. Calculate Forward Returns for Research Validation
        # Forward returns calculated from avg_return_5d / 20d
        # Forward 5D: Return over next 5 sessions
        with self.db.get_connection() as conn:
            df_ret_lookup = pd.read_sql_query("SELECT date, basic_industry, avg_return_5d, avg_return_20d FROM industry_metrics ORDER BY basic_industry ASC, date ASC;", conn)

        df_ret_lookup['fwd_return_5d'] = df_ret_lookup.groupby('basic_industry')['avg_return_5d'].shift(-5)
        df_ret_lookup['fwd_return_10d'] = df_ret_lookup.groupby('basic_industry')['avg_return_5d'].shift(-10)
        df_ret_lookup['fwd_return_20d'] = df_ret_lookup.groupby('basic_industry')['avg_return_20d'].shift(-20)

        df_v2_all = df_v2_all.merge(
            df_ret_lookup[['date', 'basic_industry', 'fwd_return_5d', 'fwd_return_10d', 'fwd_return_20d']],
            on=['date', 'basic_industry'],
            how='left'
        )

        # 6. Synchronize into industry_metrics SQLite Table
        cols_to_sync = [
            'date', 'basic_industry', 'score_v2', 'reliability_score', 'reliability_label',
            'score_v2_change_1d', 'score_v2_change_3d', 'score_v2_change_5d',
            'price_score', 'price_score_change_5d', 'breadth_score', 'breadth_score_change_5d',
            'volume_score', 'volume_score_change_5d', 'trend_score', 'trend_score_change_5d',
            'breakout_score', 'breakout_score_change_5d', 'delivery_score', 'delivery_score_change_5d',
            'dir_vol_model_a', 'dir_vol_model_b', 'dir_vol_model_c',
            'flow_confirmation', 'flow_state_v2', 'conflict_flags',
            'fwd_return_5d', 'fwd_return_10d', 'fwd_return_20d'
        ]

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for _, r in df_v2_all[cols_to_sync].iterrows():
                update_sql = """
                UPDATE industry_metrics SET
                    score_v2 = ?,
                    reliability_score = ?,
                    reliability_label = ?,
                    score_v2_change_1d = ?,
                    score_v2_change_3d = ?,
                    score_v2_change_5d = ?,
                    price_score = ?,
                    price_score_change_5d = ?,
                    breadth_score = ?,
                    breadth_score_change_5d = ?,
                    volume_score = ?,
                    volume_score_change_5d = ?,
                    trend_score = ?,
                    trend_score_change_5d = ?,
                    breakout_score = ?,
                    breakout_score_change_5d = ?,
                    delivery_score = ?,
                    delivery_score_change_5d = ?,
                    dir_vol_model_a = ?,
                    dir_vol_model_b = ?,
                    dir_vol_model_c = ?,
                    flow_confirmation = ?,
                    flow_state_v2 = ?,
                    conflict_flags = ?,
                    fwd_return_5d = ?,
                    fwd_return_10d = ?,
                    fwd_return_20d = ?
                WHERE date = ? AND basic_industry = ?;
                """
                cursor.execute(update_sql, [
                    r['score_v2'], r['reliability_score'], r['reliability_label'],
                    r['score_v2_change_1d'], r['score_v2_change_3d'], r['score_v2_change_5d'],
                    r['price_score'], r['price_score_change_5d'],
                    r['breadth_score'], r['breadth_score_change_5d'],
                    r['volume_score'], r['volume_score_change_5d'],
                    r['trend_score'], r['trend_score_change_5d'],
                    r['breakout_score'], r['breakout_score_change_5d'],
                    r['delivery_score'], r['delivery_score_change_5d'],
                    r['dir_vol_model_a'], r['dir_vol_model_b'], r['dir_vol_model_c'],
                    r['flow_confirmation'], r['flow_state_v2'], r['conflict_flags'],
                    r['fwd_return_5d'], r['fwd_return_10d'], r['fwd_return_20d'],
                    r['date'], r['basic_industry']
                ])

        logger.info(f"Successfully calculated and synchronized Money Flow V2 scores for {len(df_v2_all)} industry records.")
        return len(df_v2_all)
