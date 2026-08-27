"""
Phase 13A: Full-History Deterministic Feature Matrix & Target Rebuild Engine.
Recalculates all point-in-time stock and industry factors across the entire 365-session dataset.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any

from database.db import Database
from research.engine.factor_engine import compute_all_stock_factors
from research.engine.industry_factors import compute_industry_factor_matrix
from research.engine.forecasting_targets import compute_forecasting_targets

def rebuild_full_history_features_and_targets(
    db: Database
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Rebuilds complete deterministic feature history and multi-horizon forward targets.
    """
    print("\n[Rebuild Engine] Loading expanded price history from SQLite...")
    with db.get_connection() as conn:
        df_prices = pd.read_sql_query("""
            SELECT dp.*, s.industry, s.basic_industry 
            FROM daily_prices dp
            JOIN stocks s ON dp.symbol = s.symbol
            WHERE s.active = 1 AND s.basic_industry != 'UNKNOWN'
            ORDER BY dp.symbol ASC, dp.date ASC;
        """, conn)
        df_stocks = pd.read_sql_query("SELECT * FROM stocks WHERE active = 1;", conn)
        df_bench = pd.read_sql_query("SELECT date, close FROM market_benchmark ORDER BY date ASC;", conn)

    print(f"[Rebuild Engine] Loaded {len(df_prices):,} price records across {df_prices['date'].nunique()} trading sessions.")

    # 1. Compute Point-in-Time Stock Factors
    print("[Rebuild Engine] Computing point-in-time stock factor matrix...")
    df_stk_factors = compute_all_stock_factors(df_prices, df_bench)

    # 2. Compute Industry Factor Matrix
    print("[Rebuild Engine] Aggregating industry factor matrix across 135 Basic Industries...")
    df_ind_matrix = compute_industry_factor_matrix(df_stk_factors, df_bench)

    # 3. Compute Forward Targets (5D, 10D, 20D, 30D)
    print("[Rebuild Engine] Calculating multi-horizon forward returns and benchmark excess returns...")
    df_targets, df_stk_targets = compute_forecasting_targets(df_prices, df_bench)

    return df_prices, df_stocks, df_bench, df_stk_factors, df_ind_matrix, df_targets
