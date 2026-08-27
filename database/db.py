"""
Database manager and query helper methods for SQLite using standard library sqlite3.
Supports batch inserts, transactions, upserts, and safe concurrency.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import numpy as np
import datetime

from config.settings import DATABASE_PATH, SQLITE_TIMEOUT
from database.schema import ALL_TABLE_DDLS, INDEXES

logger = logging.getLogger(__name__)


class Database:
    """
    Thread-safe Database connection and repository manager.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = Path(db_path) if db_path else DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection with WAL mode and timeout."""
        conn = sqlite3.connect(self.db_path, timeout=SQLITE_TIMEOUT)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def initialize_schema(self):
        """Creates all tables and indexes if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for ddl in ALL_TABLE_DDLS:
                cursor.execute(ddl)
            for idx in INDEXES:
                cursor.execute(idx)
            conn.commit()
        logger.info(f"Initialized database schema at {self.db_path}")

    def insert_or_replace_df(self, table_name: str, df: pd.DataFrame, chunk_size: int = 50000):
        """
        Inserts or replaces rows from DataFrame into the given SQLite table with high-throughput chunking.
        """
        if df.empty:
            return 0

        cols = df.columns.tolist()
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join(cols)
        query = f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"

        total_inserted = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for start_idx in range(0, len(df), chunk_size):
                chunk = df.iloc[start_idx : start_idx + chunk_size].replace({np.nan: None})
                records = [tuple(r) for r in chunk.itertuples(index=False, name=None)]
                cursor.executemany(query, records)
                conn.commit()
                total_inserted += len(records)

        logger.debug(f"Inserted/Replaced {total_inserted} rows into {table_name}")
        return total_inserted

    def insert_or_ignore_df(self, table_name: str, df: pd.DataFrame):
        """
        Inserts rows from DataFrame into the given SQLite table, ignoring existing keys.
        """
        if df.empty:
            return 0

        cols = df.columns.tolist()
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join(cols)
        query = f"INSERT OR IGNORE INTO {table_name} ({col_names}) VALUES ({placeholders})"

        records = df.where(pd.notnull(df), None).to_records(index=False).tolist()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, records)
            conn.commit()
            rowcount = len(records)

        logger.debug(f"Inserted {rowcount} rows (ignored duplicates) into {table_name}")
        return rowcount

    def log_pipeline_event(self, stage: str, status: str, trade_date: Optional[str] = None,
                           records_processed: int = 0, message: str = ""):
        """Records an execution event in pipeline_logs."""
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
        INSERT INTO pipeline_logs (timestamp, stage, trade_date, status, records_processed, message)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        with self.get_connection() as conn:
            conn.execute(query, (ts, stage, trade_date, status, records_processed, message))
            conn.commit()

    def get_existing_price_dates(self) -> List[str]:
        """Returns sorted list of distinct trading dates present in daily_prices."""
        query = "SELECT DISTINCT date FROM daily_prices ORDER BY date ASC;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [r['date'] for r in rows]

    def get_existing_benchmark_dates(self) -> List[str]:
        """Returns sorted list of distinct trading dates in market_benchmark."""
        query = "SELECT DISTINCT date FROM market_benchmark ORDER BY date ASC;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
        return [r['date'] for r in rows]

    def get_active_stocks(self) -> pd.DataFrame:
        """Returns all active stocks in DataFrame."""
        query = "SELECT symbol, company_name, isin, series, industry, basic_industry, active FROM stocks WHERE active = 1;"
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn)

    def get_daily_prices(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                          symbols: Optional[List[str]] = None) -> pd.DataFrame:
        """Retrieves historical prices within date range and optional symbol filter."""
        conditions = []
        params = []
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        if symbols:
            placeholders = ", ".join(["?"] * len(symbols))
            conditions.append(f"symbol IN ({placeholders})")
            params.extend(symbols)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM daily_prices {where_clause} ORDER BY date ASC, symbol ASC;"
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_benchmark_prices(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Retrieves benchmark prices."""
        conditions = []
        params = []
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM market_benchmark {where_clause} ORDER BY date ASC;"
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_latest_trading_date(self) -> Optional[str]:
        """Returns the most recent date in daily_prices."""
        query = "SELECT MAX(date) AS max_date FROM daily_prices;"
        with self.get_connection() as conn:
            row = conn.execute(query).fetchone()
            return row['max_date'] if row and row['max_date'] else None

    def get_latest_industry_metrics(self, trade_date: Optional[str] = None) -> pd.DataFrame:
        """Returns industry metrics for the latest date or given date."""
        if trade_date is None:
            trade_date = self.get_latest_trading_date()
        if not trade_date:
            return pd.DataFrame()

        query = "SELECT * FROM industry_metrics WHERE date = ? ORDER BY score_today DESC;"
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=[trade_date])

    def get_latest_stock_metrics(self, trade_date: Optional[str] = None) -> pd.DataFrame:
        """Returns stock metrics joined with stock basic_industry for the latest date or given date."""
        if trade_date is None:
            trade_date = self.get_latest_trading_date()
        if not trade_date:
            return pd.DataFrame()

        query = """
        SELECT sm.*, s.company_name, s.industry, s.basic_industry
        FROM stock_metrics sm
        LEFT JOIN stocks s ON sm.symbol = s.symbol
        WHERE sm.date = ?
        ORDER BY sm.leadership_score DESC;
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=[trade_date])

    
    def get_stocks_by_industry(self, industry_name: str, trade_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieves all active constituent stocks belonging to a specific basic_industry (or industry).
        Includes stock metadata and latest technical metrics if available.
        Returns complete constituent list without arbitrary limits, stably sorted.
        """
        if trade_date is None:
            trade_date = self.get_latest_trading_date()

        with self.get_connection() as conn:
            query = """
            SELECT 
                s.symbol,
                s.company_name,
                s.industry,
                s.basic_industry,
                s.series,
                s.active,
                sm.close,
                sm.return_1d,
                sm.return_5d,
                sm.return_20d,
                sm.rs_5d,
                sm.rs_20d,
                sm.volume_ratio,
                sm.turnover_ratio,
                sm.high_proximity,
                sm.trend_stack,
                sm.above_20ema,
                sm.above_50ema,
                sm.above_200ema,
                sm.is_breakout_20d,
                sm.dist_ema20,
                sm.leadership_score
            FROM stocks s
            LEFT JOIN stock_metrics sm ON s.symbol = sm.symbol AND sm.date = ?
            WHERE s.active = 1 AND (s.basic_industry = ? OR s.industry = ?)
            ORDER BY COALESCE(sm.leadership_score, 0) DESC, s.company_name ASC;
            """
            df = pd.read_sql_query(query, conn, params=[trade_date, industry_name, industry_name])
        return df

    def get_company_multi_industry_records(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """Retrieves multi-industry tags and business segments for a stock or all stocks."""
        with self.get_connection() as conn:
            if symbol:
                query = "SELECT * FROM company_multi_industry_classification WHERE symbol = ? ORDER BY id ASC;"
                return pd.read_sql_query(query, conn, params=[symbol])
            else:
                query = "SELECT * FROM company_multi_industry_classification ORDER BY symbol ASC, id ASC;"
                return pd.read_sql_query(query, conn)

    def get_conglomerate_companies(self) -> pd.DataFrame:
        """Retrieves diversified conglomerate companies operating across multiple sectors/subsectors."""
        with self.get_connection() as conn:
            query = """
            SELECT symbol, company_name, COUNT(DISTINCT niche_subsector) as total_segments,
                   GROUP_CONCAT(DISTINCT niche_subsector) as segments_list,
                   GROUP_CONCAT(DISTINCT macro_sector) as sectors_list
            FROM company_multi_industry_classification
            GROUP BY symbol, company_name
            HAVING total_segments > 1
            ORDER BY total_segments DESC, symbol ASC;
            """
            return pd.read_sql_query(query, conn)


    def get_data_health_stats(self) -> Dict[str, Any]:
        """Calculates operational health and statistics for the database."""
        with self.get_connection() as conn:
            total_stocks = conn.execute("SELECT COUNT(*) FROM stocks;").fetchone()[0]
            active_stocks = conn.execute("SELECT COUNT(*) FROM stocks WHERE active = 1;").fetchone()[0]
            unclassified_stocks = conn.execute("SELECT COUNT(*) FROM stocks WHERE basic_industry = 'UNKNOWN';").fetchone()[0]
            total_prices = conn.execute("SELECT COUNT(*) FROM daily_prices;").fetchone()[0]
            distinct_price_dates = conn.execute("SELECT COUNT(DISTINCT date) FROM daily_prices;").fetchone()[0]
            distinct_benchmark_dates = conn.execute("SELECT COUNT(DISTINCT date) FROM market_benchmark;").fetchone()[0]
            distinct_industries = conn.execute("SELECT COUNT(DISTINCT basic_industry) FROM industry_metrics;").fetchone()[0]
            last_date = conn.execute("SELECT MAX(date) FROM daily_prices;").fetchone()[0]
            last_log = conn.execute("SELECT * FROM pipeline_logs ORDER BY id DESC LIMIT 1;").fetchone()

        db_size_mb = (self.db_path.stat().st_size / (1024 * 1024)) if self.db_path.exists() else 0.0

        return {
            "total_stocks": total_stocks,
            "active_stocks": active_stocks,
            "unclassified_stocks": unclassified_stocks,
            "total_price_records": total_prices,
            "distinct_price_dates": distinct_price_dates,
            "distinct_benchmark_dates": distinct_benchmark_dates,
            "distinct_industries": distinct_industries,
            "latest_trade_date": last_date,
            "database_size_mb": round(db_size_mb, 2),
            "last_pipeline_log": dict(last_log) if last_log else None
        }

    # -------------------------------------------------------------------------
    # Custom Trading Industry & Segment Query Methods (Layer 2)
    # -------------------------------------------------------------------------
    def get_custom_industries(self) -> List[str]:
        """Returns sorted list of distinct custom trading industries."""
        query = "SELECT DISTINCT custom_industry FROM custom_industry_classification ORDER BY custom_industry ASC;"
        with self.get_connection() as conn:
            rows = conn.execute(query).fetchall()
            return [r[0] for r in rows if r[0]]

    def get_custom_segments(self, custom_industry: str) -> Dict[str, int]:
        """Returns dictionary of segments and constituent stock counts for a custom trading industry."""
        query = """
        SELECT COALESCE(custom_segment, 'Unsegmented') as segment, COUNT(*) as cnt
        FROM custom_industry_classification
        WHERE custom_industry = ?
        GROUP BY COALESCE(custom_segment, 'Unsegmented')
        ORDER BY cnt DESC;
        """
        with self.get_connection() as conn:
            rows = conn.execute(query, [custom_industry]).fetchall()
            return {r[0]: r[1] for r in rows}

    def get_stocks_by_custom_industry(self, custom_industry: str, trade_date: Optional[str] = None) -> pd.DataFrame:
        """Retrieves all constituent stocks mapped to a custom trading industry joined with technical metrics."""
        if trade_date is None:
            trade_date = self.get_latest_trading_date()

        query = """
        SELECT 
            s.symbol,
            s.company_name,
            s.industry as official_sector,
            s.basic_industry as official_basic_industry,
            cic.custom_industry,
            cic.custom_segment,
            cic.notes as classification_notes,
            cic.classification_source,
            sm.close,
            sm.return_1d,
            sm.return_5d,
            sm.return_20d,
            sm.rs_5d,
            sm.rs_20d,
            sm.volume_ratio,
            sm.turnover_ratio,
            sm.high_proximity,
            sm.trend_stack,
            sm.above_20ema,
            sm.above_50ema,
            sm.above_200ema,
            sm.is_breakout_20d,
            sm.leadership_score
        FROM custom_industry_classification cic
        JOIN stocks s ON cic.symbol = s.symbol
        LEFT JOIN stock_metrics sm ON s.symbol = sm.symbol AND sm.date = ?
        WHERE cic.custom_industry = ? AND s.active = 1
        ORDER BY COALESCE(sm.leadership_score, 0) DESC, s.company_name ASC;
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=[trade_date, custom_industry])

    def get_stocks_by_custom_segment(self, custom_industry: str, custom_segment: Optional[str] = None, trade_date: Optional[str] = None) -> pd.DataFrame:
        """Retrieves constituent stocks for a specific custom trading segment."""
        df_all = self.get_stocks_by_custom_industry(custom_industry, trade_date=trade_date)
        if df_all.empty or custom_segment is None or custom_segment == 'All Segments':
            return df_all
        return df_all[df_all['custom_segment'] == custom_segment].reset_index(drop=True)

    def get_custom_classification_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Returns custom classification dictionary for a specific symbol if configured."""
        query = "SELECT * FROM custom_industry_classification WHERE symbol = ?;"
        with self.get_connection() as conn:
            row = conn.execute(query, [symbol.strip().upper()]).fetchone()
            if row:
                cols = [c[0] for c in conn.execute("PRAGMA table_info(custom_industry_classification);").fetchall()]
                return dict(zip(cols, row))
        return None

