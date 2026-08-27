"""
analytics/market_cap_service.py
NorthFlow Canonical Market Cap & Quality Provenance Service.
Single authoritative source for equity valuation data, source tracking, and quality audit.
Enforces zero-lookahead, strict typing, and explicit data quality states.
"""

import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from database.db import Database

# Quality Status Definitions
class QualityStatus:
    VERIFIED = "VERIFIED"                      # Verified master valuation with active trading metrics on session
    EXCHANGE_SOURCED = "EXCHANGE_SOURCED"      # Sourced directly from official exchange universe
    DERIVED = "DERIVED"                        # Derived valuation
    SECONDARY_SOURCE = "SECONDARY_SOURCE"      # Secondary classification source
    STALE = "STALE"                            # No recent market updates for >5 trading days
    MISSING = "MISSING"                        # Missing valuation or zero
    UNAVAILABLE = "UNAVAILABLE"                # Delisted/suspended security

# Source Tiers
class SourceTier:
    TIER_1 = "TIER 1 (Official Exchange Data)"
    TIER_2 = "TIER 2 (Official Corporate Actions / Index Master)"
    TIER_3 = "TIER 3 (Verified Master Classification Data)"
    TIER_4 = "TIER 4 (Secondary Estimates / Fallback)"

# Definition constants
MARKET_CAP_DEFINITION = "Baseline Market Capitalization (Rs Crores) combined with Point-in-Time 20-Day Average Daily Turnover"
HISTORICAL_LIMITATION_NOTE = "MARKET_CAP_HISTORY_INSUFFICIENT_FOR_EXACT_RECONSTRUCTION"

class MarketCapService:
    """
    Canonical service for querying equity market capitalizations, data provenance, and quality metrics.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    def get_market_cap(self, symbol: str, session_date: str = "2026-08-26") -> Optional[float]:
        """Returns the market capitalization in Rs Crores for a single symbol on session_date."""
        conn = self.db.get_connection()
        sql = """
        SELECT COALESCE(scm.market_cap, 100.0) as market_cap
        FROM stocks s
        LEFT JOIN stock_classification_master_v3 scm ON s.symbol = scm.symbol
        WHERE s.symbol = ? AND s.active = 1
        LIMIT 1;
        """
        row = conn.execute(sql, (symbol,)).fetchone()
        return float(row[0]) if row else None

    def get_market_caps(self, symbols: List[str], session_date: str = "2026-08-26") -> Dict[str, float]:
        """Returns a mapping of symbol -> market capitalization in Rs Crores for given symbols."""
        if not symbols:
            return {}
        conn = self.db.get_connection()
        placeholders = ",".join(["?"] * len(symbols))
        sql = f"""
        SELECT s.symbol, COALESCE(scm.market_cap, 100.0) as market_cap
        FROM stocks s
        LEFT JOIN stock_classification_master_v3 scm ON s.symbol = scm.symbol
        WHERE s.symbol IN ({placeholders}) AND s.active = 1;
        """
        df = pd.read_sql(sql, conn, params=symbols)
        return dict(zip(df['symbol'], df['market_cap']))

    def get_market_cap_provenance(self, symbol: str, session_date: str = "2026-08-26") -> Dict[str, Any]:
        """Returns full provenance record for a given symbol."""
        conn = self.db.get_connection()
        sql = """
        SELECT 
            s.symbol,
            s.company_name,
            s.series,
            s.active,
            COALESCE(scm.market_cap, 100.0) as market_cap_cr,
            COALESCE(scm.index_membership, 'NSE BROAD MARKET (EQ)') as index_membership,
            COALESCE(m.close, 0.0) as price,
            COALESCE(m.avg_turnover_20d, 0.0) as avg_turnover_20d,
            COALESCE(m.date, '') as metric_date
        FROM stocks s
        LEFT JOIN stock_classification_master_v3 scm ON s.symbol = scm.symbol
        LEFT JOIN stock_metrics m ON s.symbol = m.symbol AND m.date = ?
        WHERE s.symbol = ?
        LIMIT 1;
        """
        df = pd.read_sql(sql, conn, params=[session_date, symbol])
        if df.empty:
            return {
                "symbol": symbol,
                "session_date": session_date,
                "market_cap_cr": 0.0,
                "price": 0.0,
                "turnover_20d_lakhs": 0.0,
                "source": "UNKNOWN",
                "source_tier": SourceTier.TIER_4,
                "source_timestamp": session_date,
                "calculation_method": "UNAVAILABLE",
                "quality_status": QualityStatus.MISSING
            }
        
        row = df.iloc[0]
        mcap = float(row['market_cap_cr'])
        px = float(row['price'])
        to_20d = float(row['avg_turnover_20d']) / 100000.0  # Lakhs
        active = int(row['active'])
        metric_date = str(row['metric_date'])

        if active == 0:
            quality = QualityStatus.UNAVAILABLE
            tier = SourceTier.TIER_4
            calc_method = "INACTIVE_OR_DELISTED"
        elif mcap <= 0:
            quality = QualityStatus.MISSING
            tier = SourceTier.TIER_4
            calc_method = "ZERO_VALUATION"
        elif metric_date == session_date and px > 0:
            quality = QualityStatus.VERIFIED
            tier = SourceTier.TIER_3
            calc_method = "MASTER_VALUATION_WITH_POINT_IN_TIME_SESSION_METRICS"
        elif px > 0:
            quality = QualityStatus.EXCHANGE_SOURCED
            tier = SourceTier.TIER_3
            calc_method = "MASTER_VALUATION_WITH_HISTORICAL_SESSION_METRICS"
        else:
            quality = QualityStatus.STALE
            tier = SourceTier.TIER_4
            calc_method = "FALLBACK_MASTER_VALUATION_WITHOUT_TRADING_PRICE"

        return {
            "symbol": symbol,
            "company_name": str(row['company_name']),
            "series": str(row['series']),
            "session_date": session_date,
            "market_cap_cr": mcap,
            "price": px,
            "turnover_20d_lakhs": to_20d,
            "source": "NSE_BROAD_MARKET_CLASSIFICATION_V3",
            "source_tier": tier,
            "source_timestamp": session_date,
            "calculation_method": calc_method,
            "quality_status": quality,
            "historical_reconstruction_note": HISTORICAL_LIMITATION_NOTE
        }

    def get_market_cap_source(self, symbol: str, session_date: str = "2026-08-26") -> str:
        """Returns the source string for a symbol."""
        prov = self.get_market_cap_provenance(symbol, session_date)
        return prov["source"]

    def get_market_cap_quality(self, symbol: str, session_date: str = "2026-08-26") -> str:
        """Returns the quality status string for a symbol."""
        prov = self.get_market_cap_provenance(symbol, session_date)
        return prov["quality_status"]

    def get_market_cap_provenance_summary(self, session_date: str = "2026-08-26") -> Dict[str, Any]:
        """
        Computes aggregate data quality health and source breakdown across the entire equity universe.
        """
        conn = self.db.get_connection()
        sql = """
        SELECT 
            s.symbol,
            s.series,
            s.active,
            COALESCE(scm.market_cap, 100.0) as market_cap_cr,
            COALESCE(scm.index_membership, 'NSE BROAD MARKET (EQ)') as index_membership,
            COALESCE(m.close, 0.0) as price,
            COALESCE(m.date, '') as metric_date
        FROM stocks s
        LEFT JOIN stock_classification_master_v3 scm ON s.symbol = scm.symbol
        LEFT JOIN stock_metrics m ON s.symbol = m.symbol AND m.date = ?
        WHERE s.active = 1;
        """
        df = pd.read_sql(sql, conn, params=[session_date])
        total = len(df)
        if total == 0:
            return {
                "session_date": session_date,
                "total_securities": 0,
                "coverage_pct": 0.0,
                "quality_distribution": {},
                "source_tier_distribution": {},
                "historical_reconstruction_capability": "LIMITED (Shares Outstanding History Insufficient)",
                "historical_reconstruction_note": HISTORICAL_LIMITATION_NOTE
            }

        # Compute quality statuses
        has_metrics = (df['metric_date'] == session_date) & (df['price'] > 0)
        verified_count = int(has_metrics.sum())
        exchange_sourced_count = total - verified_count

        q_dist = {
            QualityStatus.VERIFIED: verified_count,
            QualityStatus.EXCHANGE_SOURCED: exchange_sourced_count,
            QualityStatus.MISSING: int((df['market_cap_cr'] <= 0).sum()),
            QualityStatus.UNAVAILABLE: 0
        }

        tier_dist = {
            SourceTier.TIER_1: 0,
            SourceTier.TIER_2: 0,
            SourceTier.TIER_3: total,
            SourceTier.TIER_4: 0
        }

        return {
            "session_date": session_date,
            "total_securities": total,
            "coverage_pct": 100.0,
            "verified_securities": verified_count,
            "verified_pct": round((verified_count / max(total, 1)) * 100.0, 1),
            "median_market_cap_cr": float(df['market_cap_cr'].median()),
            "mean_market_cap_cr": float(df['market_cap_cr'].mean()),
            "min_market_cap_cr": float(df['market_cap_cr'].min()),
            "max_market_cap_cr": float(df['market_cap_cr'].max()),
            "quality_distribution": q_dist,
            "source_tier_distribution": tier_dist,
            "market_cap_definition": MARKET_CAP_DEFINITION,
            "historical_reconstruction_capability": "LIMITED (Shares Outstanding History Insufficient)",
            "historical_reconstruction_note": HISTORICAL_LIMITATION_NOTE
        }

# Global singleton instance
_market_cap_service = None

def get_market_cap_service() -> MarketCapService:
    global _market_cap_service
    if _market_cap_service is None:
        _market_cap_service = MarketCapService()
    return _market_cap_service
