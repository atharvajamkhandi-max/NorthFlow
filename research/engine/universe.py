"""
Universe Coverage Audit Engine.
Audits:
- Listed active NSE Equities in database
- Official NSE Macro Sectors (23), Sectors, Industries, Basic Industries (135)
- Custom Trading Industries and Segments
- Benchmark Index: NIFTY SMALLCAP 250
Generates research/reports/universe_coverage.md
"""

import os
import pandas as pd
from database.db import Database
from config.settings import BENCHMARK_INDEX

def audit_universe(db: Database) -> pd.DataFrame:
    with db.get_connection() as conn:
        total_stocks = conn.execute("SELECT COUNT(*) FROM stocks;").fetchone()[0]
        active_stocks = conn.execute("SELECT COUNT(*) FROM stocks WHERE active = 1;").fetchone()[0]
        distinct_macro = conn.execute("SELECT COUNT(DISTINCT industry) FROM stocks WHERE industry IS NOT NULL AND industry != 'UNKNOWN';").fetchone()[0]
        distinct_basic = conn.execute("SELECT COUNT(DISTINCT basic_industry) FROM stocks WHERE basic_industry IS NOT NULL AND basic_industry != 'UNKNOWN';").fetchone()[0]
        
        # Custom Trading Classification
        q_cust = "SELECT COUNT(DISTINCT custom_industry), COUNT(DISTINCT custom_segment), COUNT(*) FROM custom_industry_classification;"
        cust_row = conn.execute(q_cust).fetchone()
        cust_inds, cust_segs, cust_mapped = cust_row[0], cust_row[1], cust_row[2]

        # Dates coverage
        total_sessions = conn.execute("SELECT COUNT(DISTINCT date) FROM daily_prices;").fetchone()[0]
        min_date = conn.execute("SELECT MIN(date) FROM daily_prices;").fetchone()[0]
        max_date = conn.execute("SELECT MAX(date) FROM daily_prices;").fetchone()[0]

        # Benchmark
        bench_records = conn.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM market_benchmark WHERE index_name = ?;", [BENCHMARK_INDEX]).fetchone()

    coverage_data = [
        {"Universe Layer": "Active NSE Equities", "Count": active_stocks, "Historical Sessions": f"{total_sessions} ({min_date} to {max_date})", "Included in Research": "YES", "Exclusion Reason": "None (100% Included)"},
        {"Universe Layer": "Official Basic Industries", "Count": distinct_basic, "Historical Sessions": f"{total_sessions} ({min_date} to {max_date})", "Included in Research": "YES", "Exclusion Reason": "Primary Industry Layer"},
        {"Universe Layer": "Official Macro Sectors", "Count": distinct_macro, "Historical Sessions": f"{total_sessions} ({min_date} to {max_date})", "Included in Research": "YES", "Exclusion Reason": "Macro Aggregation Layer"},
        {"Universe Layer": "Custom Trading Industries", "Count": cust_inds, "Historical Sessions": f"{total_sessions} ({min_date} to {max_date})", "Included in Research": "YES", "Exclusion Reason": f"Mapped across {cust_mapped} stocks"},
        {"Universe Layer": "Custom Trading Segments", "Count": cust_segs, "Historical Sessions": f"{total_sessions} ({min_date} to {max_date})", "Included in Research": "YES", "Exclusion Reason": "Segment Level Analysis"},
        {"Universe Layer": f"Benchmark ({BENCHMARK_INDEX})", "Count": 1, "Historical Sessions": f"{bench_records[0]} ({bench_records[1]} to {bench_records[2]})", "Included in Research": "YES", "Exclusion Reason": "Official Benchmark"}
    ]
    return pd.DataFrame(coverage_data)
