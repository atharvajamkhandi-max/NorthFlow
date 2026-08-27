"""
storage/decision_ledger_query_service.py
High-Performance Read-Only Query Service for Historical Decision Timelines.
Never calls or modifies quantitative models or scoring algorithms.
"""

import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional
from pathlib import Path

DEFAULT_LEDGER_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "decision_ledger.db"

class DecisionLedgerQueryService:
    """
    Provides fast, indexed read-only queries for historical decision timelines.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_LEDGER_DB_PATH

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=15.0)
        return conn

    @staticmethod
    def _resolve_period_limit(period: str) -> Optional[int]:
        """Translates human periods into approximate trading sessions."""
        mapping = {
            "1M": 21,
            "3M": 63,
            "6M": 125,
            "12M": 250,
            "24M": 500,
            "ALL": None
        }
        return mapping.get(period.upper(), 250)

    def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        period: str = "12M",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        model_version: str = "MODEL_V3.2_FROZEN"
    ) -> pd.DataFrame:
        """
        Retrieves point-in-time decision timeline for any Stock, Industry, or Sector.
        Supports exact entity_id, exact entity_name, and smart token search.
        """
        if not self.db_path.exists():
            return pd.DataFrame()

        clean_id = entity_id.strip()
        etype = entity_type.strip().upper()

        limit_clause = ""
        limit_val = self._resolve_period_limit(period)
        if limit_val and not (start_date and end_date):
            limit_clause = f"LIMIT {limit_val}"

        # 1. Exact Match
        params = [etype, clean_id, clean_id, model_version]
        conditions = ["entity_type = ?", "(entity_id = ? OR entity_name = ?)", "model_version = ?"]

        if start_date:
            conditions.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("trade_date <= ?")
            params.append(end_date)

        query = f"""
        SELECT trade_date, entity_type, entity_id, entity_name, model_version,
               score, rating_action, flow_state, early_radar_score, alert_level,
               prob_1d, prob_3d, prob_5d, expected_lead_days, breadth_50,
               confidence_score, risk_score, regime_label, parent_industry,
               parent_sector, close_price, row_hash
        FROM historical_decision_ledger
        WHERE {" AND ".join(conditions)}
        ORDER BY trade_date DESC
        {limit_clause}
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)

        # 2. Token / Substring Fallback
        if df.empty:
            tokens = [t.strip() for t in clean_id.replace("&", " ").replace(",", " ").replace("-", " ").split() if len(t.strip()) >= 3]
            if tokens:
                like_clauses = " OR ".join(["entity_id LIKE ? OR entity_name LIKE ?"] * len(tokens))
                token_params = [etype]
                for t in tokens:
                    token_params.extend([f"%{t}%", f"%{t}%"])
                token_params.append(model_version)

                token_conds = [f"entity_type = ?", f"({like_clauses})", "model_version = ?"]
                if start_date:
                    token_conds.append("trade_date >= ?")
                    token_params.append(start_date)
                if end_date:
                    token_conds.append("trade_date <= ?")
                    token_params.append(end_date)

                token_query = f"""
                SELECT trade_date, entity_type, entity_id, entity_name, model_version,
                       score, rating_action, flow_state, early_radar_score, alert_level,
                       prob_1d, prob_3d, prob_5d, expected_lead_days, breadth_50,
                       confidence_score, risk_score, regime_label, parent_industry,
                       parent_sector, close_price, row_hash
                FROM historical_decision_ledger
                WHERE {" AND ".join(token_conds)}
                ORDER BY trade_date DESC
                {limit_clause}
                """
                with self._get_connection() as conn:
                    df = pd.read_sql_query(token_query, conn, params=token_params)

        if not df.empty:
            # If multiple entities matched, keep the most frequent entity_id
            if df["entity_id"].nunique() > 1:
                top_ent = df["entity_id"].value_counts().index[0]
                df = df[df["entity_id"] == top_ent].copy()

            df = df.sort_values(by="trade_date", ascending=True).reset_index(drop=True)

        return df

    def get_stock_history(self, symbol: str, period: str = "12M", start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        return self.get_entity_history("STOCK", symbol.strip().upper(), period=period, start_date=start_date, end_date=end_date)

    def get_industry_history(self, industry_name: str, period: str = "12M", start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        return self.get_entity_history("INDUSTRY", industry_name.strip(), period=period, start_date=start_date, end_date=end_date)

    def get_sector_history(self, sector_name: str, period: str = "12M", start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        return self.get_entity_history("SECTOR", sector_name.strip(), period=period, start_date=start_date, end_date=end_date)

    def get_daily_snapshot(self, trade_date: str, entity_type: Optional[str] = None) -> pd.DataFrame:
        """Retrieves complete decision snapshot across all entities for a specific date."""
        if not self.db_path.exists():
            return pd.DataFrame()

        params = [trade_date]
        conditions = ["trade_date = ?"]
        if entity_type:
            conditions.append("entity_type = ?")
            params.append(entity_type.upper())

        query = f"""
        SELECT trade_date, entity_type, entity_id, entity_name, model_version,
               score, rating_action, flow_state, early_radar_score, alert_level,
               prob_1d, prob_3d, prob_5d, expected_lead_days, breadth_50,
               confidence_score, risk_score, regime_label, parent_industry,
               parent_sector, close_price, row_hash
        FROM historical_decision_ledger
        WHERE {" AND ".join(conditions)}
        ORDER BY score DESC
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)

        return df

    def get_rating_transitions(self, entity_type: str, entity_id: str, period: str = "12M") -> pd.DataFrame:
        """
        Extracts discrete rating transition events (e.g. BUY -> STRONG BUY).
        """
        df = self.get_entity_history(entity_type, entity_id, period=period)
        if df.empty or len(df) < 2:
            return df

        df["prev_rating"] = df["rating_action"].shift(1)
        df["prev_score"] = df["score"].shift(1)
        df["prev_date"] = df["trade_date"].shift(1)
        
        transitions = df[df["rating_action"] != df["prev_rating"]].copy()
        return transitions.dropna(subset=["prev_rating"]).reset_index(drop=True)
