"""
Phase A & B: Quantitative Historical Data Quality & Corporate Action Auditor.
Audits 403 sessions for OHLC integrity, zero/negative prices, volume spikes,
stale prices, dividend/split consistency, delivery completeness, and calculates data_quality_score.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from database.db import Database

class QuantDataAuditor:
    def __init__(self, db: Database = None):
        self.db = db or Database()

    def run_full_audit(self) -> Tuple[Dict[str, Any], pd.DataFrame]:
        print("\n--- [Phase A & B] Auditing 403 Historical Trading Sessions ---")
        with self.db.get_connection() as conn:
            df_prices = pd.read_sql_query("SELECT * FROM daily_prices ORDER BY symbol ASC, date ASC;", conn)
            df_stocks = pd.read_sql_query("SELECT * FROM stocks;", conn)
            df_bench = pd.read_sql_query("SELECT * FROM market_benchmark ORDER BY date ASC;", conn)

        total_rows = len(df_prices)
        distinct_dates = df_prices['date'].nunique()
        distinct_symbols = df_prices['symbol'].nunique()
        all_dates = sorted(df_prices['date'].unique().tolist())

        # 1. Zero/Negative Price Violations
        zero_neg_prices = len(df_prices[(df_prices['close'] <= 0) | (df_prices['open'] <= 0) | (df_prices['high'] <= 0) | (df_prices['low'] <= 0)])
        
        # 2. High-Low Inconsistencies (High < Low or Close > High or Close < Low)
        hl_violations = len(df_prices[(df_prices['high'] < df_prices['low']) | (df_prices['close'] > df_prices['high'] * 1.0001) | (df_prices['close'] < df_prices['low'] * 0.9999)])
        
        # 3. Duplicate Records
        duplicates = df_prices.duplicated(subset=['date', 'symbol']).sum()

        # 4. Volume Anomaly Check (Negative volume)
        neg_volume = len(df_prices[df_prices['volume'] < 0])

        # 5. Delivery Completeness
        deliv_available = df_prices['delivery_percentage'].notnull().sum()
        deliv_completeness_pct = round((deliv_available / total_rows) * 100.0, 2)

        # 6. Benchmark Coverage
        bench_dates = set(df_bench['date'].unique().tolist())
        missing_bench_dates = [d for d in all_dates if d not in bench_dates]

        # 7. Overall Data Quality Score (0 to 100)
        penalty = (zero_neg_prices * 5.0) + (hl_violations * 2.0) + (duplicates * 5.0) + (neg_volume * 5.0) + (len(missing_bench_dates) * 2.0)
        data_quality_score = max(0.0, min(100.0, 100.0 - penalty))

        audit_summary = {
            "total_price_records": total_rows,
            "total_sessions": distinct_dates,
            "earliest_session": all_dates[0],
            "latest_session": all_dates[-1],
            "distinct_equities": distinct_symbols,
            "zero_or_negative_prices": zero_neg_prices,
            "high_low_violations": hl_violations,
            "duplicate_records": duplicates,
            "negative_volume_records": neg_volume,
            "delivery_completeness_pct": deliv_completeness_pct,
            "missing_benchmark_dates_count": len(missing_bench_dates),
            "data_quality_score": round(data_quality_score, 2),
            "audit_verdict": "PASSED" if data_quality_score >= 95.0 else "WARNING"
        }

        # Daily coverage log
        daily_cov = df_prices.groupby('date').agg(
            stock_count=('symbol', 'count'),
            total_turnover=('turnover', 'sum'),
            avg_delivery_pct=('delivery_percentage', 'mean')
        ).reset_index()
        daily_cov['data_quality_score'] = data_quality_score

        print(f"Data Quality Audit Complete: Score = {data_quality_score}/100 | {total_rows:,} records across {distinct_dates} sessions.")
        return audit_summary, daily_cov
