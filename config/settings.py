"""
Configuration settings for Indian Stock Market Industry Money Flow Screener.
All weights, thresholds, file paths, and operational parameters are centralized here.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "market_flow.db"
INDUSTRY_OVERRIDES_PATH = DATA_DIR / "industry_overrides.csv"
SEED_CLASSIFICATIONS_PATH = DATA_DIR / "seed_classifications.json"
CUSTOM_INDUSTRY_MAPPING_PATH = DATA_DIR / "custom_industry_mapping.csv"
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration
SQLITE_TIMEOUT = 30.0

# Equity Filters
VALID_SERIES = ["EQ", "BE", "BZ", "SM", "ST", "SZ", "DR"]  # 100% of all Mainboard and SME equity securities

# Benchmark Index for Relative Strength
BENCHMARK_INDEX = "NIFTY SMALLCAP 250"

# Backfill Settings
DEFAULT_BACKFILL_DAYS = 250
MIN_DAYS_FOR_200EMA = 200
MIN_DAYS_FOR_METRICS = 20

# Industry Ranking & Breadth Thresholds
MIN_STOCKS_FOR_RANKING = 5  # Below this threshold, industry is marked 'LOW SAMPLE'
MIN_STOCKS_ABSOLUTE = 1

# Money Flow Scoring Weights (Sum = 100.0)
SCORE_WEIGHTS = {
    "rs_5d": 30.0,            # 5-day Relative Strength vs NIFTY SMALLCAP 250
    "rs_20d": 20.0,           # 20-day Relative Strength vs NIFTY SMALLCAP 250
    "breadth": 20.0,          # Composite Breadth (% > EMA20, % > EMA50, % positive)
    "volume_expansion": 15.0, # Average 20D Volume Ratio
    "breakout_breadth": 10.0, # % of constituents breaking 20-day highs
    "delivery_strength": 5.0  # Average Delivery % (reweighted if unavailable)
}

# Institutional Stock Leadership Scoring Weights (Within Industry)
STOCK_LEADERSHIP_WEIGHTS = {
    "near_high": 25.0,        # Proximity to 20-session / 52-week High
    "rs_20d": 25.0,           # 20-day Relative Strength vs NIFTY SMALLCAP 250
    "trend_stack": 15.0,      # Moving Average Alignment (Price > 20 EMA > 50 EMA)
    "rs_5d": 15.0,            # 5-day Relative Strength vs NIFTY SMALLCAP 250
    "turnover_quality": 10.0, # Rupee Turnover Expansion on Positive Days
    "breakout": 10.0          # 20-day Base Breakout Quality
}

# Rotation State Classification Thresholds
ROTATION_THRESHOLDS = {
    "STRONG": {
        "min_score": 75.0,
        "min_5d_change": 0.0
    },
    "STRENGTHENING": {
        "min_score": 60.0,
        "min_5d_change": 5.0
    },
    "EMERGING": {
        "min_5d_change": 10.0,
        "min_breadth_gain": 15.0
    },
    "WEAKENING": {
        "max_5d_change": -5.0
    },
    "EXHAUSTION": {
        "min_score_was": 75.0,
        "max_5d_change": -10.0
    },
    "WEAK": {
        "max_score": 40.0
    }
}

# Daily Pipeline Schedule (Checkpoints in Asia/Kolkata)
DAILY_UPDATE_TIMES = [
    "17:00",
    "18:00",
    "19:00",
    "20:00"
]
TIMEZONE = "Asia/Kolkata"

# Market Regime Classification Thresholds
MARKET_REGIME_CONFIG = {
    "BULLISH": {
        "min_pct_positive_5d": 55.0,
        "min_pct_ema20_breadth": 50.0,
        "min_bull_bear_ratio": 1.3
    },
    "BULLISH_NARROW": {
        "min_pct_positive_5d": 45.0,
        "max_pct_ema20_breadth": 50.0
    },
    "ROTATION": {
        "min_emerging_count": 25,
        "min_cooling_count": 20
    },
    "BEARISH": {
        "max_pct_positive_5d": 40.0,
        "max_pct_ema20_breadth": 40.0
    }
}

# Industry Universe Configuration
MARKET_OVERVIEW_INDUSTRY_UNIVERSE = "OFFICIAL_BASIC_INDUSTRY"

# ==============================================================================
# MONEY FLOW METHODOLOGY V2 (RESEARCH CONFIGURATION)
# ==============================================================================
# Initial Research Component Weights (Decomposed 6-Factor Model)
MONEY_FLOW_V2_WEIGHTS = {
    "price": 0.30,              # Relative Strength vs NIFTY Smallcap 250 (3D, 5D, 10D, 20D)
    "breadth": 0.25,            # Constituent Participation (% > EMA20/50, % > 0) + Breadth Momentum
    "directional_volume": 0.20, # Volume Ratio Expansion Spread (Up vs Down Days)
    "trend": 0.10,              # Moving Average Trend Stack Alignment (Price > EMA20 > EMA50 > EMA200)
    "breakout": 0.10,           # 20-Day Base Breakouts with Volume Confirmation
    "delivery": 0.05            # Delivery Accumulation Confirmation
}

# 2D Flow State Classification Thresholds (Current Strength vs Acceleration)
FLOW_STATE_V2_CONFIG = {
    "EARLY_INFLOW": {
        "min_score": 40.0,
        "max_score": 70.0,
        "min_5d_change": 8.0,
        "min_breadth_5d_change": 10.0
    },
    "ACCELERATING": {
        "min_score": 60.0,
        "min_5d_change": 4.0,
        "min_volume_score": 55.0
    },
    "STRONG_LEADER": {
        "min_score": 75.0,
        "min_5d_change": 0.0,
        "min_breadth_score": 65.0
    },
    "MATURE_STRONG": {
        "min_score": 75.0,
        "max_5d_change": 0.0,
        "min_5d_change": -5.0
    },
    "COOLING": {
        "min_score": 55.0,
        "max_5d_change": -5.0
    },
    "DISTRIBUTION": {
        "max_price_score": 40.0,
        "max_volume_score": 40.0,
        "max_directional_spread": -15.0
    },
    "WEAK": {
        "max_score": 40.0,
        "max_5d_change": 0.0
    }
}

# Flow Confirmation Thresholds
FLOW_CONFIRMATION_CONFIG = {
    "HIGH_THRESHOLD": 60.0,
    "MODERATE_THRESHOLD": 50.0,
    "DIVERGENCE_PRICE_HIGH": 70.0,
    "DIVERGENCE_BREADTH_LOW": 40.0,
    "DIVERGENCE_VOL_SPREAD_LOW": -20.0
}
