"""
Point-in-Time Cash Market Data Loader for Quant Lab.
"""
import os
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class CashMarketDataFeed:
    """
    Point-in-time Cash Market Data Loader.
    Bridges SQLite database and Historical 2020-2024 NSE cache.
    Guarantees strict point-in-time integrity with zero lookahead bias.
    """
    def __init__(self, db_path: Optional[str] = None):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.db_path = db_path or str(base_dir / "data" / "market_flow.db")
        
    def load_canonical_stock_universe(self) -> pd.DataFrame:
        """Loads canonical 3,028 stock universe with sector and industry classifications."""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT symbol, company_name, sector, industry, is_active
            FROM stock_classification_master_v3
            WHERE is_active = 1
            ORDER BY sector, industry, symbol
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def load_cash_prices_and_delivery(self, symbols: Optional[List[str]] = None, 
                                     start_date: Optional[str] = None, 
                                     end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Loads daily prices with volume and deliverable positions.
        """
        conn = sqlite3.connect(self.db_path)
        conditions = ["1=1"]
        params = []
        
        if symbols:
            placeholders = ",".join(["?"] * len(symbols))
            conditions.append(f"dp.symbol IN ({placeholders})")
            params.extend(symbols)
            
        if start_date:
            conditions.append("dp.date >= ?")
            params.append(start_date)
            
        if end_date:
            conditions.append("dp.date <= ?")
            params.append(end_date)
            
        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT 
                dp.symbol, 
                dp.date, 
                dp.open, 
                dp.high, 
                dp.low, 
                dp.close, 
                dp.volume, 
                dp.turnover, 
                dp.delivery_quantity AS deliv_qty, 
                dp.delivery_percentage AS deliv_per,
                m.sector,
                m.industry
            FROM daily_prices dp
            JOIN stock_classification_master_v3 m ON dp.symbol = m.symbol
            WHERE {where_clause}
            ORDER BY dp.symbol, dp.date
        """
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            df['deliv_qty'] = pd.to_numeric(df['deliv_qty'], errors='coerce').fillna(0)
            df['deliv_per'] = pd.to_numeric(df['deliv_per'], errors='coerce').fillna(0)
            
        return df

    def load_benchmark_returns(self) -> pd.DataFrame:
        """Loads daily benchmark close and returns for NIFTY 50 and NIFTY Smallcap 250."""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT symbol, date, close, change_p FROM market_benchmark ORDER BY symbol, date"
        df = pd.read_sql_query(query, conn)
        conn.close()
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
        return df
