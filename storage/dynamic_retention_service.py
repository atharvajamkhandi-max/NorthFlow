"""
storage/dynamic_retention_service.py
Dynamic Trading Calendar Retention Window Service.
Computes calendar-driven rolling windows (e.g. latest 60 trading sessions ending at T)
accounting for weekends, exchange holidays, and dynamic calendar progression.
Never hard-codes calendar dates.
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

DEFAULT_MARKET_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "market_flow.db"

class DynamicRetentionService:
    """
    Computes dynamic rolling trading-session windows relative to latest valid session.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_MARKET_DB_PATH

    def get_valid_trading_sessions(self, limit: Optional[int] = None) -> List[str]:
        """
        Retrieves ordered list of all distinct valid trading dates (newest first).
        Holidays, weekends, and non-trading days do not count as sessions.
        """
        if not self.db_path.exists():
            return []

        limit_clause = f"LIMIT {int(limit)}" if limit else ""
        query = f"SELECT DISTINCT date FROM daily_prices ORDER BY date DESC {limit_clause}"
        
        with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True) as conn:
            cur = conn.cursor()
            cur.execute(query)
            sessions = [r[0] for r in cur.fetchall()]

        return sessions

    def resolve_hot_operational_window(self, target_sessions: int = 60) -> Dict[str, Any]:
        """
        Dynamically calculates the latest N valid trading sessions window.
        Returns:
            - latest_session (T)
            - hot_cutoff_session (T - target_sessions + 1)
            - total_hot_sessions
            - hot_session_list
        """
        sessions = self.get_valid_trading_sessions()
        if not sessions:
            return {"error": "No trading sessions found"}

        hot_sessions = sessions[:target_sessions]
        latest_date = hot_sessions[0]
        cutoff_date = hot_sessions[-1]

        return {
            "latest_trading_session": latest_date,
            "hot_cutoff_session": cutoff_date,
            "target_session_count": target_sessions,
            "actual_hot_sessions": len(hot_sessions),
            "hot_sessions_list": hot_sessions,
            "is_dynamic": True
        }

    def resolve_trailing_window_for_date(self, eval_date: str, window_size: int = 20) -> List[str]:
        """
        Resolves trailing N valid trading sessions strictly on or before eval_date.
        """
        query = f"SELECT DISTINCT date FROM daily_prices WHERE date <= ? ORDER BY date DESC LIMIT {int(window_size)}"
        with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True) as conn:
            cur = conn.cursor()
            cur.execute(query, (eval_date,))
            trailing = [r[0] for r in cur.fetchall()]

        return trailing
