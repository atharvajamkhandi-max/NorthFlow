"""
Market Regime Synthesis & Overview Analytics Engine (Phase 3).
Evaluates aggregate industry behaviour across all granular industries to determine:
- Market Regime (BULLISH, BULLISH BUT NARROW, ROTATION, NEUTRAL, BEARISH)
- Quantitative Signal Confidence (0-100%)
- Breadth & Participation Metrics
- Emerging, Cooling, Leading, and Laggard Industry Rankings
- Grounded, evidence-based Dynamic Market Summary
Benchmark: NIFTY SMALLCAP 250
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from database.db import Database
from config.settings import MARKET_REGIME_CONFIG, BENCHMARK_INDEX

logger = logging.getLogger(__name__)


class MarketRegimeAnalyzer:
    """
    Synthesizes cross-sectional industry data into high-level market regime intelligence.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    def analyze_session(self, trade_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyzes market regime for a given trading session using observable industry metrics.
        Guarantees zero look-ahead bias by only utilizing records for trade_date.
        """
        if trade_date is None:
            trade_date = self.db.get_latest_trading_date()

        if not trade_date:
            return self._empty_regime_result(trade_date)

        df_ind = self.db.get_latest_industry_metrics(trade_date=trade_date)
        if df_ind.empty:
            return self._empty_regime_result(trade_date)

        total_industries = len(df_ind)
        status_counts = df_ind['status'].value_counts().to_dict()

        # Categorize Status Counts
        strong_count = status_counts.get('STRONG', 0)
        strengthening_count = status_counts.get('STRENGTHENING', 0)
        emerging_count = status_counts.get('EMERGING', 0)
        neutral_count = status_counts.get('NEUTRAL', 0)
        cooling_count = status_counts.get('COOLING', 0) + status_counts.get('WEAKENING', 0) + status_counts.get('EXHAUSTION', 0)
        weak_count = status_counts.get('WEAK', 0) + status_counts.get('DISTRIBUTION', 0)

        bullish_count = strong_count + strengthening_count
        bearish_count = weak_count

        # Breadth & Participation
        pct_positive_1d = float((df_ind['avg_return_1d'] > 0).mean() * 100.0)
        pct_positive_5d = float((df_ind['avg_return_5d'] > 0).mean() * 100.0)
        pct_positive_20d = float((df_ind['avg_return_20d'] > 0).mean() * 100.0)

        pct_above_ema20 = float((df_ind['ema20_breadth'] >= 50.0).mean() * 100.0)
        pct_above_ema50 = float((df_ind['ema50_breadth'] >= 50.0).mean() * 100.0)
        avg_market_breadth_20 = float(df_ind['ema20_breadth'].mean())

        avg_volume_ratio = float(df_ind['avg_volume_ratio'].mean())
        breakout_industries_count = int((df_ind['breakout_count'] > 0).sum())
        total_breakouts = int(df_ind['breakout_count'].sum())

        avg_5d_score_change = float(df_ind['score_change_5d'].mean())
        median_rs_5d = float(df_ind['industry_rs_5d'].median())

        # Regime Determination Rules
        bull_bear_ratio = (bullish_count + emerging_count * 0.5) / max(1, bearish_count + cooling_count * 0.5)
        
        regime = "NEUTRAL"
        confidence = 50.0

        cfg = MARKET_REGIME_CONFIG
        if pct_positive_5d >= cfg["BULLISH"]["min_pct_positive_5d"] and pct_above_ema20 >= cfg["BULLISH"]["min_pct_ema20_breadth"] and bull_bear_ratio >= cfg["BULLISH"]["min_bull_bear_ratio"]:
            regime = "BULLISH"
            confidence = min(95.0, 60.0 + (pct_positive_5d - 50.0) * 0.5 + (pct_above_ema20 - 50.0) * 0.4)
        elif pct_positive_5d >= cfg["BULLISH_NARROW"]["min_pct_positive_5d"] and pct_above_ema20 < cfg["BULLISH_NARROW"]["max_pct_ema20_breadth"]:
            regime = "BULLISH BUT NARROW"
            confidence = min(90.0, 55.0 + abs(pct_positive_5d - pct_above_ema20) * 0.8)
        elif emerging_count >= cfg["ROTATION"]["min_emerging_count"] and cooling_count >= cfg["ROTATION"]["min_cooling_count"]:
            regime = "ROTATION"
            confidence = min(90.0, 60.0 + (emerging_count + cooling_count) * 0.3)
        elif pct_positive_5d <= cfg["BEARISH"]["max_pct_positive_5d"] and pct_above_ema20 <= cfg["BEARISH"]["max_pct_ema20_breadth"]:
            regime = "BEARISH"
            confidence = min(95.0, 60.0 + (50.0 - pct_positive_5d) * 0.6 + (50.0 - pct_above_ema20) * 0.4)
        else:
            regime = "NEUTRAL"
            confidence = max(50.0, 100.0 - abs(bullish_count - bearish_count) * 2.0)

        # Ranked Subsets
        top_emerging = df_ind.sort_values('score_change_5d', ascending=False).head(10)
        top_cooling = df_ind.sort_values('score_change_5d', ascending=True).head(10)
        top_leaders = df_ind.sort_values('score_today', ascending=False).head(10)
        top_laggards = df_ind.sort_values('score_today', ascending=True).head(10)

        # Dynamic Evidence-Grounded Summary Generation
        emerging_names = ", ".join(top_emerging['basic_industry'].head(3).tolist())
        cooling_names = ", ".join(top_cooling['basic_industry'].head(3).tolist())
        leader_names = ", ".join(top_leaders['basic_industry'].head(3).tolist())

        summary_lines = []
        if regime == "BULLISH":
            summary_lines.append(f"Market participation is broad and institutional capital is expanding across granular industries.")
        elif regime == "BULLISH BUT NARROW":
            summary_lines.append(f"Market strength is selective and concentrated in specific leading groups rather than broad-based.")
        elif regime == "ROTATION":
            summary_lines.append(f"Active capital rotation is occurring under the surface, with money moving into early emerging groups while mature sectors cool.")
        elif regime == "BEARISH":
            summary_lines.append(f"Market breadth is deteriorating with widespread distribution across the majority of industries.")
        else:
            summary_lines.append(f"The market is in a balanced consolidation phase with neutral momentum dispersion.")

        summary_lines.append(
            f"**{bullish_count}** of {total_industries} tracked industries are currently bullish or strengthening, while **{cooling_count}** are cooling and **{bearish_count}** are weak. "
            f"**{pct_positive_5d:.0f}%** of industries maintain positive 5-day returns, with **{pct_above_ema20:.0f}%** showing >50% constituents above their 20 EMA."
        )

        if emerging_names:
            summary_lines.append(f"Momentum acceleration is strongest in **{emerging_names}**, while deceleration is noticeable in **{cooling_names}**.")

        summary_lines.append(
            f"Overall market condition relative to {BENCHMARK_INDEX}: **{regime}** (Signal Confidence: **{confidence:.0f}%**)."
        )

        dynamic_summary = "\n\n".join(summary_lines)

        return {
            "trade_date": trade_date,
            "regime": regime,
            "confidence": round(confidence, 1),
            "total_industries": total_industries,
            "status_counts": status_counts,
            "bullish_count": bullish_count,
            "strengthening_count": strengthening_count,
            "emerging_count": emerging_count,
            "neutral_count": neutral_count,
            "cooling_count": cooling_count,
            "bearish_count": bearish_count,
            "pct_positive_1d": round(pct_positive_1d, 1),
            "pct_positive_5d": round(pct_positive_5d, 1),
            "pct_positive_20d": round(pct_positive_20d, 1),
            "pct_above_ema20": round(pct_above_ema20, 1),
            "pct_above_ema50": round(pct_above_ema50, 1),
            "avg_market_breadth_20": round(avg_market_breadth_20, 1),
            "avg_volume_ratio": round(avg_volume_ratio, 2),
            "breakout_industries_count": breakout_industries_count,
            "total_breakouts": total_breakouts,
            "avg_5d_score_change": round(avg_5d_score_change, 1),
            "median_rs_5d": round(median_rs_5d, 2),
            "top_emerging": top_emerging,
            "top_cooling": top_cooling,
            "top_leaders": top_leaders,
            "top_laggards": top_laggards,
            "dynamic_summary": dynamic_summary,
            "df_ind": df_ind
        }

    def get_historical_regimes(self, limit: int = 40) -> pd.DataFrame:
        """
        Calculates daily aggregate regime distribution across all historical sessions in SQLite.
        """
        query = """
        SELECT 
            date,
            status,
            COUNT(*) as count
        FROM industry_metrics
        GROUP BY date, status
        ORDER BY date ASC;
        """
        with self.db.get_connection() as conn:
            df_raw = pd.read_sql_query(query, conn)

        if df_raw.empty:
            return pd.DataFrame()

        df_piv = df_raw.pivot(index='date', columns='status', values='count').fillna(0)
        df_piv = df_piv.reset_index()
        return df_piv.tail(limit)

    def _empty_regime_result(self, trade_date: Optional[str]) -> Dict[str, Any]:
        return {
            "trade_date": trade_date or "N/A",
            "regime": "NEUTRAL",
            "confidence": 0.0,
            "total_industries": 0,
            "status_counts": {},
            "bullish_count": 0,
            "strengthening_count": 0,
            "emerging_count": 0,
            "neutral_count": 0,
            "cooling_count": 0,
            "bearish_count": 0,
            "pct_positive_1d": 0.0,
            "pct_positive_5d": 0.0,
            "pct_positive_20d": 0.0,
            "pct_above_ema20": 0.0,
            "pct_above_ema50": 0.0,
            "avg_market_breadth_20": 0.0,
            "avg_volume_ratio": 1.0,
            "breakout_industries_count": 0,
            "total_breakouts": 0,
            "avg_5d_score_change": 0.0,
            "median_rs_5d": 0.0,
            "top_emerging": pd.DataFrame(),
            "top_cooling": pd.DataFrame(),
            "top_leaders": pd.DataFrame(),
            "top_laggards": pd.DataFrame(),
            "dynamic_summary": "No market data available to synthesize regime.",
            "df_ind": pd.DataFrame()
        }
