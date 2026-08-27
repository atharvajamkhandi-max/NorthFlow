"""
storage/decision_ledger.py
Optimized, Immutable, Point-in-Time Historical Decision Ledger for Stocks, Industries, and Sectors.
Dimensional star schema (dim_entities, dim_model_versions, fact_historical_decisions, historical_decision_ledger VIEW).
Strictly append-only (WORM). Never feeds back into models or alters production scoring logic.
"""

import os
import sqlite3
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pandas as pd

DEFAULT_LEDGER_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "decision_ledger.db"

class DecisionLedger:
    """
    Manages the optimized SQLite-backed Historical Decision Ledger.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_LEDGER_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self):
        """Initializes the normalized decision ledger schema, indexes, and backward-compatible VIEW."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS dim_entities (
                entity_key INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                entity_name TEXT NOT NULL,
                parent_industry TEXT,
                parent_sector TEXT,
                UNIQUE (entity_type, entity_id)
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS dim_model_versions (
                model_key INTEGER PRIMARY KEY AUTOINCREMENT,
                version_name TEXT NOT NULL UNIQUE
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS fact_historical_decisions (
                trade_date TEXT NOT NULL,
                entity_key INTEGER NOT NULL,
                model_key INTEGER NOT NULL,
                score REAL NOT NULL,
                rating_action TEXT NOT NULL,
                flow_state TEXT,
                early_radar_score REAL,
                alert_level TEXT,
                prob_1d REAL,
                prob_3d REAL,
                prob_5d REAL,
                expected_lead_days REAL,
                breadth_50 REAL,
                confidence_score REAL,
                risk_score REAL,
                regime_label TEXT,
                close_price REAL,
                row_hash BLOB NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (trade_date, entity_key, model_key),
                FOREIGN KEY (entity_key) REFERENCES dim_entities(entity_key),
                FOREIGN KEY (model_key) REFERENCES dim_model_versions(model_key)
            );
            """)

            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_fact_entity_date 
            ON fact_historical_decisions (entity_key, trade_date DESC);
            """)

            cur.execute("""
            CREATE VIEW IF NOT EXISTS historical_decision_ledger AS
            SELECT 
                f.trade_date,
                e.entity_type,
                e.entity_id,
                e.entity_name,
                m.version_name AS model_version,
                f.score,
                f.rating_action,
                f.flow_state,
                f.early_radar_score,
                f.alert_level,
                f.prob_1d,
                f.prob_3d,
                f.prob_5d,
                f.expected_lead_days,
                f.breadth_50,
                f.confidence_score,
                f.risk_score,
                f.regime_label,
                e.parent_industry,
                e.parent_sector,
                f.close_price,
                lower(hex(f.row_hash)) AS row_hash,
                f.created_at
            FROM fact_historical_decisions f
            JOIN dim_entities e ON f.entity_key = e.entity_key
            JOIN dim_model_versions m ON f.model_key = m.model_key;
            """)
            conn.commit()

    @staticmethod
    def compute_row_hash(
        trade_date: str,
        entity_type: str,
        entity_id: str,
        model_version: str,
        score: float,
        rating_action: str,
        flow_state: Optional[str] = None,
        early_radar_score: Optional[float] = None
    ) -> str:
        """
        Computes a deterministic SHA-256 checksum for a decision record.
        Detects any unauthorized post-hoc mutations to historical beliefs.
        """
        score_str = f"{float(score):.2f}" if score is not None else "0.00"
        radar_str = f"{float(early_radar_score):.2f}" if early_radar_score is not None else "NULL"
        flow_str = str(flow_state or "NULL").strip().upper()
        canonical_str = (
            f"{str(trade_date).strip()}|"
            f"{str(entity_type).strip().upper()}|"
            f"{str(entity_id).strip()}|"
            f"{str(model_version).strip()}|"
            f"{score_str}|"
            f"{str(rating_action).strip().upper()}|"
            f"{flow_str}|"
            f"{radar_str}"
        )
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def record_decisions(self, records: List[Dict[str, Any]]) -> int:
        """
        Appends new decision snapshots into normalized dimensions and fact table.
        Uses INSERT OR IGNORE to guarantee immutability (zero overwrite).
        """
        if not records:
            return 0

        with self._get_connection() as conn:
            cur = conn.cursor()

            # Ensure entities exist in dim_entities
            cur.execute("SELECT entity_type, entity_id, entity_key FROM dim_entities")
            ent_map = {(r[0], r[1]): r[2] for r in cur.fetchall()}

            # Ensure model versions exist in dim_model_versions
            cur.execute("SELECT version_name, model_key FROM dim_model_versions")
            ver_map = {r[0]: r[1] for r in cur.fetchall()}

            new_entities = []
            new_versions = []

            for r in records:
                etype = str(r["entity_type"]).strip().upper()
                eid = str(r["entity_id"]).strip()
                ename = str(r.get("entity_name", eid)).strip()
                p_ind = str(r.get("parent_industry")) if r.get("parent_industry") else None
                p_sec = str(r.get("parent_sector")) if r.get("parent_sector") else None
                mver = str(r.get("model_version", "MODEL_V3.2_FROZEN")).strip()

                if (etype, eid) not in ent_map:
                    new_entities.append((etype, eid, ename, p_ind, p_sec))
                    ent_map[(etype, eid)] = -1  # Placeholder

                if mver not in ver_map:
                    new_versions.append((mver,))
                    ver_map[mver] = -1

            if new_entities:
                cur.executemany("""
                INSERT OR IGNORE INTO dim_entities (entity_type, entity_id, entity_name, parent_industry, parent_sector)
                VALUES (?, ?, ?, ?, ?)
                """, new_entities)
                conn.commit()
                cur.execute("SELECT entity_type, entity_id, entity_key FROM dim_entities")
                ent_map = {(r[0], r[1]): r[2] for r in cur.fetchall()}

            if new_versions:
                cur.executemany("INSERT OR IGNORE INTO dim_model_versions (version_name) VALUES (?)", new_versions)
                conn.commit()
                cur.execute("SELECT version_name, model_key FROM dim_model_versions")
                ver_map = {r[0]: r[1] for r in cur.fetchall()}

            # Prepare fact rows
            fact_rows = []
            for r in records:
                tdate = str(r["trade_date"]).strip()
                etype = str(r["entity_type"]).strip().upper()
                eid = str(r["entity_id"]).strip()
                mver = str(r.get("model_version", "MODEL_V3.2_FROZEN")).strip()
                ekey = ent_map.get((etype, eid))
                mkey = ver_map.get(mver)
                
                score = float(r["score"]) if r.get("score") is not None else 50.0
                rating_action = str(r.get("rating_action", "NEUTRAL")).strip().upper()
                flow_state = str(r["flow_state"]).strip().upper() if r.get("flow_state") else None
                radar_score = float(r["early_radar_score"]) if r.get("early_radar_score") is not None else None

                row_hash_hex = r.get("row_hash") or self.compute_row_hash(
                    trade_date=tdate, entity_type=etype, entity_id=eid,
                    model_version=mver, score=score, rating_action=rating_action,
                    flow_state=flow_state, early_radar_score=radar_score
                )
                hash_blob = bytes.fromhex(row_hash_hex) if row_hash_hex else b""

                fact_rows.append((
                    tdate, ekey, mkey, score, rating_action, flow_state,
                    radar_score, r.get("alert_level"), r.get("prob_1d"), r.get("prob_3d"),
                    r.get("prob_5d"), r.get("expected_lead_days"), r.get("breadth_50"),
                    r.get("confidence_score"), r.get("risk_score"), r.get("regime_label"),
                    r.get("close_price"), hash_blob
                ))

            insert_sql = """
            INSERT OR IGNORE INTO fact_historical_decisions (
                trade_date, entity_key, model_key, score, rating_action, flow_state,
                early_radar_score, alert_level, prob_1d, prob_3d, prob_5d,
                expected_lead_days, breadth_50, confidence_score, risk_score,
                regime_label, close_price, row_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            cur.executemany(insert_sql, fact_rows)
            inserted_cnt = cur.rowcount
            conn.commit()

        return inserted_cnt

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Recalculates cryptographic row hashes across the entire ledger.
        Returns a verification report detecting any tampered records.
        """
        with self._get_connection() as conn:
            df = pd.read_sql_query(
                "SELECT trade_date, entity_type, entity_id, model_version, score, rating_action, flow_state, early_radar_score, row_hash FROM historical_decision_ledger",
                conn
            )

        if df.empty:
            return {"total_records": 0, "valid_hashes": 0, "tampered_records": 0, "status": "EMPTY"}

        valid_count = 0
        tampered_ids = []

        for _, row in df.iterrows():
            expected = self.compute_row_hash(
                trade_date=row["trade_date"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                model_version=row["model_version"],
                score=row["score"],
                rating_action=row["rating_action"],
                flow_state=row["flow_state"],
                early_radar_score=row["early_radar_score"]
            )
            if expected == str(row["row_hash"]).lower():
                valid_count += 1
            else:
                tampered_ids.append(f"{row['trade_date']}|{row['entity_type']}|{row['entity_id']}")

        is_clean = (len(tampered_ids) == 0)
        return {
            "total_records": len(df),
            "valid_hashes": valid_count,
            "tampered_records": len(tampered_ids),
            "tampered_samples": tampered_ids[:5],
            "status": "PASS" if is_clean else "FAIL"
        }

    def get_ledger_stats(self) -> Dict[str, Any]:
        """Returns row counts, entity counts, date ranges, and physical file size."""
        file_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*), MIN(trade_date), MAX(trade_date), COUNT(DISTINCT trade_date) FROM historical_decision_ledger")
            total_rows, min_date, max_date, distinct_dates = cur.fetchone()
            
            cur.execute("SELECT entity_type, COUNT(*), COUNT(DISTINCT entity_id) FROM historical_decision_ledger GROUP BY entity_type")
            type_breakdown = {r[0]: {"row_count": r[1], "distinct_entities": r[2]} for r in cur.fetchall()}

        return {
            "db_path": str(self.db_path),
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "total_rows": total_rows or 0,
            "min_date": min_date or "-",
            "max_date": max_date or "-",
            "distinct_trading_sessions": distinct_dates or 0,
            "entity_breakdown": type_breakdown
        }
