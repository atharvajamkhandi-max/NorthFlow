# NSE Historical Datasets (2020 - 2024) via nselib

**Data Extraction Date**: 2026-08-23  
**Source Library**: `nselib` (Official National Stock Exchange of India API Connector)  
**Storage Location**: `research/nselib_data_2020_2024/`  
**Isolation Guarantee**: Completely segregated from production trading models and databases.

---

## Downloaded Datasets

### 1. `india_vix_2020_2024.csv`
- **Description**: Daily historical Implied Volatility Index (India VIX) spanning COVID-19 crash, bull market run, and election cycles.
- **Columns**: `TIMESTAMP`, `INDEX_NAME`, `OPEN_INDEX_VAL`, `HIGH_INDEX_VAL`, `LOW_INDEX_VAL`, `CLOSING_INDEX_VAL`, `PREV_CLOSE`, `VIX_PTS_CHG`, `VIX_PERC_CHG`.

### 2. `nifty_indices_2020_2024.csv`
- **Description**: Historical daily OHLCV and trading activity for 12 broad and sectoral benchmarks:
  - Broad: `NIFTY 50`, `NIFTY NEXT 50`, `NIFTY MIDCAP 150`, `NIFTY SMALLCAP 250`
  - Sectoral: `NIFTY BANK`, `NIFTY IT`, `NIFTY AUTO`, `NIFTY PHARMA`, `NIFTY METAL`, `NIFTY FMCG`, `NIFTY ENERGY`, `NIFTY INFRA`
- **Columns**: `INDEX_NAME`, `TIMESTAMP`, `OPEN_INDEX_VAL`, `HIGH_INDEX_VAL`, `LOW_INDEX_VAL`, `CLOSING_INDEX_VAL`, `TRADED_QTY`, `TURN_OVER`, `YEAR`.

### 3. `bulk_deals_2020_2024.csv`
- **Description**: All institutional and high-net-worth individual (HNI) transactions $> 0.5\%$ of equity share capital across all listed equities.
- **Columns**: `Date`, `Symbol`, `Security Name`, `Client Name`, `Buy/Sell`, `Quantity Traded`, `TradePrice/Wght.Avg.Price`, `Remarks`, `YEAR`.

### 4. `block_deals_2020_2024.csv`
- **Description**: All discrete large-window block transactions ($\ge ₹10\text{ Cr}$).
- **Columns**: `Date`, `Symbol`, `Security Name`, `Client Name`, `Buy/Sell`, `Quantity Traded`, `TradePrice/Wght.Avg.Price`, `YEAR`.

### 5. `short_selling_2020_2024.csv`
- **Description**: Official institutional short selling positions disclosed daily to the exchange.
- **Columns**: `Date`, `Symbol`, `Security Name`, `Quantity`, `YEAR`.
