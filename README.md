# Indian Stock Market Industry Money Flow Screener 🇮🇳

An automated, quantitative end-to-end Python system built to identify, rank, and track capital flow dynamics across **granular Indian stock-market industries** (e.g. *Wires & Cables*, *Lubricants*, *Bearings*, *Pumps & Compressors*, *Transformers*, *Electronic Manufacturing Services (EMS)*, *Aerospace & Defence*, *Railways*, *Auto Components*, *Specialty Chemicals*, *Batteries*, *Paints*, *Cement*, etc.) using the official `nselib` library, SQLite, pandas, numpy, and Streamlit.

---

## 🎯 Core Objectives

1. **Granular Industry Money Flow**: Discover where capital is concentrating beyond broad sector indices (e.g. distinguishing *Wires & Cables* or *Transformers* from broad *Capital Goods*).
2. **Early Rotation Detection**: Catch emerging momentum acceleration and volume expansion before an industry becomes an obvious market leader.
3. **Constituent Stock Leaders**: Rank the leading stocks driving each granular industry's move using a composite Stock Leadership Score.

---

## 🏛️ System Architecture

```text
                               +--------------------------+
                               | NSE India / nselib API   |
                               +--------------------------+
                                            |
                                            v
                               +--------------------------+
                               |   providers/nse_provider | (Isolated nselib wrapper & holiday filter)
                               +--------------------------+
                                            |
                                            v
                               +--------------------------+
                               |     SQLite Database      | (Resumable, idempotent data/market_flow.db)
                               +--------------------------+
                                            |
                                            v
                               +--------------------------+
                               |   Analytics Engine       | (Returns, EMAs, RS, Breadth, 20D Breakouts)
                               +--------------------------+
                                            |
                                            v
                               +--------------------------+
                               | Cross-Sectional Scoring  | (0-100 Money Flow Score & Rotation States)
                               +--------------------------+
                                            |
                                            v
                               +--------------------------+
                               | Streamlit Dashboard (UI) | (Overview, Emerging, Deep Dive, Backtest)
                               +--------------------------+
```

---

## 📁 Project Structure

```text
industry-money-flow/
├── app.py                         # Streamlit multi-page dashboard entrypoint
├── requirements.txt               # Dependencies (nselib, streamlit, plotly, pandas, etc.)
├── README.md                      # Documentation & operational guide
│
├── config/
│   ├── __init__.py
│   └── settings.py                # Weights, thresholds, database path, minimum sample sizes
│
├── data/
│   ├── industry_overrides.csv     # Manual overrides (symbol, industry, basic_industry)
│   └── seed_classifications.json  # Curated granular NSE Basic Industry taxonomy seed
│
├── database/
│   ├── __init__.py
│   ├── schema.py                  # DDL definitions & index optimization
│   └── db.py                      # Connection manager, transactions, upserts, query helpers
│
├── providers/
│   ├── __init__.py
│   └── nse_provider.py            # Normalized data layer over nselib (bhavcopy with delivery)
│
├── pipeline/
│   ├── __init__.py
│   ├── update_classification.py   # 4-tier industry classification resolution engine
│   └── update_market_data.py      # Resumable bhavcopy & benchmark ingestion engine
│
├── analytics/
│   ├── __init__.py
│   ├── stock_metrics.py           # Stock-level returns, EMAs (20, 50, 200), volume ratios, breakouts
│   ├── industry_metrics.py        # Basic industry aggregation, mean/median returns, breadths
│   ├── scoring.py                 # Cross-sectional percentile ranking & 0-100 Money Flow Scoring
│   ├── rotation.py                # 1D/3D/5D score change tracking & Rotation States (EMERGING, STRONG, etc.)
│   └── backtesting.py             # Forward 5D/10D return simulator for signal evaluation
│
├── dashboard/
│   ├── __init__.py
│   ├── overview.py                # Main Money Flow Screener table with sorting & filtering
│   ├── emerging.py                # Emerging & Fast-Improving Industries detector
│   ├── industry_detail.py         # Deep-dive view with Plotly charts, breadth history, & stock leaders
│   ├── backtest_view.py           # Strategy research & performance visualization
│   └── data_quality.py            # Data validation status, sync logs, and missing data alerts
│
├── scripts/
│   ├── initial_setup.py           # First-time setup: DB schema, stock master, 250-session backfill
│   └── daily_update.py            # Production daily pipeline for post-market automation
│
└── tests/
    ├── __init__.py
    ├── test_provider.py           # Provider parsing & holiday tests
    ├── test_database.py           # DB constraints & duplicate prevention tests
    ├── test_classification.py     # 4-tier resolution priority tests
    ├── test_market_data.py        # Resumable ingestion tests
    ├── test_stock_metrics.py      # Zero look-ahead bias breakout & EMA tests
    ├── test_industry_metrics.py   # Aggregation & breadth tests
    ├── test_scoring.py            # Money flow normalization & leadership tests
    └── test_rotation.py           # Rotation state classification tests
```

---

## ⚡ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/<your-username>/industry-money-flow.git
   cd industry-money-flow
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Quick Start Guide

### Step 1: Run Initial Setup & Historical Backfill
Bootstrap the system with 30 trading sessions for quick verification (or 250 sessions for complete 200 EMA support):
```bash
# 30-day initial test
python scripts/initial_setup.py --days 30

# Full 250-day setup
python scripts/initial_setup.py --days 250
```
> The download is **resumable** and **idempotent**. If interrupted, rerunning continues from the missing dates.

### Step 2: Launch the Streamlit Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Step 3: Run Post-Market Daily Update
After market close (typically after 16:00 IST), run:
```bash
python scripts/daily_update.py
```
This automatically fetches the latest NSE trading session, recomputes all metrics, scores, and rotation states, and logs the execution.

---

## 📊 Money Flow Score Methodology

The **Industry Money Flow Score (0–100)** represents cross-sectional evidence of capital flow inferred from multi-dimensional market behaviour:

| Factor | Weight | Description |
| :--- | :---: | :--- |
| **5D Relative Strength** | **30%** | Industry 5-day mean return vs NIFTY 50 benchmark |
| **20D Relative Strength** | **20%** | Industry 20-day mean return vs NIFTY 50 benchmark |
| **Composite Breadth** | **20%** | 40% (% > EMA20) + 30% (% > EMA50) + 30% (% Positive) |
| **Volume Expansion** | **15%** | Average volume relative to previous 20-session average |
| **Breakout Breadth** | **10%** | % of constituents breaking above previous 20-session highs |
| **Delivery Strength** | **5%** | Average delivery % (dynamically reweighted if unavailable) |

Each factor is ranked cross-sectionally via percentile ranks across all eligible industries on that date, combined using the configurable weights in `config/settings.py`, and scaled to `[0.0, 100.0]`.

---

## 🔄 Rotation State Classification

Industries are classified into momentum and rotation lifecycle states:

- **`EMERGING`**: Rapidly improving momentum (`Score >= 50`, `5D Score Change >= +15`, `Volume Ratio >= 1.0x`).
- **`STRONG`**: Established leader (`Score >= 75`, `5D Score Change >= 0`).
- **`STRENGTHENING`**: Steady advance (`Score 60–75`, `5D Score Change >= +5`).
- **`COOLING`**: Momentum fading from prior highs (`Past Score >= 65`, `5D Score Change <= -10`).
- **`DISTRIBUTION`**: Severe capital exit (`Score <= 55`, `5D Score Change <= -15`).
- **`WEAK`**: Depressed money flow (`Score < 45`).

---

## 🏷️ Industry Classification Resolution Hierarchy

To ensure high granularity without manual data entry for 2,000+ stocks:
```text
1. User Overrides (data/industry_overrides.csv)   [Top Priority]
        ↓
2. Curated NSE Basic Industry Seed (data/seed_classifications.json)
        ↓
3. Official NSE Index Classification (archives.nseindia.com)
        ↓
4. UNKNOWN (No silent guessing)
```

To add or override any stock classification, edit `data/industry_overrides.csv`:
```csv
symbol,industry,basic_industry
POLYCAB,Capital Goods,Wires & Cables
CASTROLIND,Oil Gas & Consumable Fuels,Lubricants
```

---

## 🧪 Testing

Run the comprehensive unit test suite:
```bash
pytest tests/ -v
```

All calculations strictly enforce **zero look-ahead bias** (today's high/close is excluded when computing historical breakout reference prices and moving average volumes).
