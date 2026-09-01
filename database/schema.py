"""
Database Schema Definitions for SQLite.
Optimized for time-series financial analysis with composite indexes,
strict constraints, and audit logging.
Maintains two distinct layers:
1. Official NSE Classification (in stocks table)
2. Custom Trading & Segment Classification (in custom_industry_classification table)
"""

CREATE_STOCKS_TABLE = """
CREATE TABLE IF NOT EXISTS stocks (
    symbol TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    isin TEXT,
    series TEXT DEFAULT 'EQ',
    industry TEXT DEFAULT 'UNKNOWN',
    basic_industry TEXT DEFAULT 'UNKNOWN',
    active INTEGER DEFAULT 1,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_DAILY_PRICES_TABLE = """
CREATE TABLE IF NOT EXISTS daily_prices (
    date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    series TEXT DEFAULT 'EQ',
    open REAL,
    high REAL,
    low REAL,
    close REAL NOT NULL,
    previous_close REAL,
    volume REAL,
    turnover REAL,
    delivery_quantity REAL,
    delivery_percentage REAL,
    PRIMARY KEY (date, symbol)
);
"""

CREATE_BENCHMARK_TABLE = """
CREATE TABLE IF NOT EXISTS market_benchmark (
    date TEXT PRIMARY KEY,
    index_name TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL NOT NULL,
    return_1d REAL,
    return_5d REAL,
    return_20d REAL
);
"""

CREATE_STOCK_METRICS_TABLE = """
CREATE TABLE IF NOT EXISTS stock_metrics (
    date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    close REAL,
    return_1d REAL,
    return_5d REAL,
    return_20d REAL,
    ema20 REAL,
    ema50 REAL,
    ema200 REAL,
    volume REAL,
    avg_volume_20d REAL,
    volume_ratio REAL,
    turnover REAL,
    avg_turnover_20d REAL,
    turnover_ratio REAL,
    turnover_quality REAL,
    high_proximity REAL,
    trend_stack REAL,
    rs_5d REAL,
    rs_20d REAL,
    is_breakout_20d INTEGER DEFAULT 0,
    above_20ema INTEGER DEFAULT 0,
    above_50ema INTEGER DEFAULT 0,
    above_200ema INTEGER DEFAULT 0,
    dist_ema20 REAL,
    dist_ema50 REAL,
    leadership_score REAL,
    PRIMARY KEY (date, symbol)
);
"""

CREATE_INDUSTRY_METRICS_TABLE = """
CREATE TABLE IF NOT EXISTS industry_metrics (
    date TEXT NOT NULL,
    industry TEXT DEFAULT 'UNKNOWN',
    basic_industry TEXT NOT NULL,
    stock_count INTEGER NOT NULL,
    avg_return_1d REAL,
    median_return_1d REAL,
    avg_return_5d REAL,
    median_return_5d REAL,
    avg_return_20d REAL,
    median_return_20d REAL,
    industry_rs_5d REAL,
    industry_rs_20d REAL,
    avg_volume_ratio REAL,
    positive_breadth REAL,
    ema20_breadth REAL,
    ema50_breadth REAL,
    ema200_breadth REAL,
    breakout_count INTEGER DEFAULT 0,
    breakout_percentage REAL DEFAULT 0.0,
    avg_delivery_percentage REAL,
    score_today REAL,
    score_1d_ago REAL,
    score_3d_ago REAL,
    score_5d_ago REAL,
    score_change_1d REAL,
    score_change_3d REAL,
    score_change_5d REAL,
    status TEXT DEFAULT 'NEUTRAL',
    is_low_sample INTEGER DEFAULT 0,
    -- V2 Methodology Research Columns --
    score_v2 REAL,
    reliability_score REAL,
    reliability_label TEXT,
    score_v2_change_1d REAL,
    score_v2_change_3d REAL,
    score_v2_change_5d REAL,
    price_score REAL,
    price_score_change_5d REAL,
    breadth_score REAL,
    breadth_score_change_5d REAL,
    volume_score REAL,
    volume_score_change_5d REAL,
    trend_score REAL,
    trend_score_change_5d REAL,
    breakout_score REAL,
    breakout_score_change_5d REAL,
    delivery_score REAL,
    delivery_score_change_5d REAL,
    dir_vol_model_a REAL,
    dir_vol_model_b REAL,
    dir_vol_model_c REAL,
    flow_confirmation TEXT,
    flow_state_v2 TEXT,
    conflict_flags TEXT,
    fwd_return_5d REAL,
    fwd_return_10d REAL,
    fwd_return_20d REAL,
    PRIMARY KEY (date, basic_industry)
);
"""

CREATE_CUSTOM_INDUSTRY_CLASSIFICATION_TABLE = """
CREATE TABLE IF NOT EXISTS custom_industry_classification (
    symbol TEXT PRIMARY KEY,
    custom_industry TEXT NOT NULL,
    custom_segment TEXT,
    classification_source TEXT DEFAULT 'MANUAL_MAP',
    confidence REAL DEFAULT 1.0,
    notes TEXT,
    updated_at TEXT NOT NULL
);
"""

CREATE_COMPANY_MULTI_INDUSTRY_CLASSIFICATION_TABLE = """
CREATE TABLE IF NOT EXISTS company_multi_industry_classification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    company_name TEXT,
    macro_sector TEXT NOT NULL,
    niche_subsector TEXT NOT NULL,
    business_segment TEXT,
    segment_tag TEXT DEFAULT 'PRIMARY',
    is_core_revenue INTEGER DEFAULT 1,
    segment_description TEXT
);
"""

CREATE_PIPELINE_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS pipeline_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    stage TEXT NOT NULL,
    trade_date TEXT,
    status TEXT NOT NULL,
    records_processed INTEGER DEFAULT 0,
    message TEXT
);
"""

INDEX_DAILY_PRICES_SYMBOL_DATE = "CREATE INDEX IF NOT EXISTS idx_daily_prices_symbol_date ON daily_prices (symbol, date);"
INDEX_STOCK_METRICS_SYMBOL = "CREATE INDEX IF NOT EXISTS idx_sm_symbol ON stock_metrics (symbol);"
INDEX_INDUSTRY_METRICS_BASIC = "CREATE INDEX IF NOT EXISTS idx_industry_metrics_industry ON industry_metrics (basic_industry);"
INDEX_STOCKS_BASIC_IND = "CREATE INDEX IF NOT EXISTS idx_stocks_basic ON stocks (basic_industry);"
INDEX_CIC_INDUSTRY = "CREATE INDEX IF NOT EXISTS idx_cic_ind ON custom_industry_classification (custom_industry);"
INDEX_CIC_SEGMENT = "CREATE INDEX IF NOT EXISTS idx_cic_seg ON custom_industry_classification (custom_industry, custom_segment);"
INDEX_MULTI_SYM = "CREATE INDEX IF NOT EXISTS idx_multi_sym ON company_multi_industry_classification (symbol);"
INDEX_MULTI_SEC = "CREATE INDEX IF NOT EXISTS idx_multi_sec ON company_multi_industry_classification (macro_sector);"
INDEX_MULTI_SUB = "CREATE INDEX IF NOT EXISTS idx_multi_sub ON company_multi_industry_classification (niche_subsector);"
INDEX_MULTI_TAG = "CREATE INDEX IF NOT EXISTS idx_multi_tag ON company_multi_industry_classification (segment_tag);"

ALL_TABLE_DDLS = [
    CREATE_STOCKS_TABLE,
    CREATE_DAILY_PRICES_TABLE,
    CREATE_BENCHMARK_TABLE,
    CREATE_STOCK_METRICS_TABLE,
    CREATE_INDUSTRY_METRICS_TABLE,
    CREATE_CUSTOM_INDUSTRY_CLASSIFICATION_TABLE,
    CREATE_COMPANY_MULTI_INDUSTRY_CLASSIFICATION_TABLE,
    CREATE_PIPELINE_LOGS_TABLE
]

INDEXES = [
    INDEX_DAILY_PRICES_SYMBOL_DATE,
    INDEX_STOCK_METRICS_SYMBOL,
    INDEX_INDUSTRY_METRICS_BASIC,
    INDEX_STOCKS_BASIC_IND,
    INDEX_CIC_INDUSTRY,
    INDEX_CIC_SEGMENT,
    INDEX_MULTI_SYM,
    INDEX_MULTI_SEC,
    INDEX_MULTI_SUB,
    INDEX_MULTI_TAG
]

