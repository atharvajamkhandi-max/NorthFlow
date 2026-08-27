# PHASE 33B — HISTORICAL DECISION MEMORY FORENSIC FIXES REPORT
### Honest Gap Visualization, Accurate Field Applicability, Clean Hover Milestones & Canonical Model-Implied Projections

**Execution Timestamp**: 2026-08-25  
**Scope**: **Isolated Presentation & Read-Only Helper Implementation** (Zero Changes to Models, Calculations, or Production DB)  
**Database**: `data/decision_ledger.db` ($96.80	ext{ MB}$, $777,946	ext{ rows}$, $250	ext{ sessions}$)  
**Hot Market Database**: `data/market_flow.db` ($99.86	ext{ MB}$, $182,244	ext{ price rows}$, $60	ext{ sessions}$)  
**Baseline Models**: [`MODEL_V3.2_FROZEN`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/config/model_v3_2_frozen.py) & [`EARLY_RADAR_V1_FROZEN`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/config/early_radar_v1_frozen.py) (**100% UNTOUCHED**)  
**Full Test Suite Status**: **208 / 208 Tests Passing (100% GREEN ✅ in 11.15s)**  

---

## 1. Executive Implementation Scorecard

```
======================================================================================================
PHASE 33B IMPLEMENTATION SCORECARD
======================================================================================================
Target Files Modified                 : dashboard/decision_memory.py (UI Presentation)
                                        tests/test_phase32_decision_memory_ui.py (Test Suite)
New Isolated Helper Created           : storage/canonical_forecast_service.py (Read-Only Forecast Query)

Historical Price Chart Fix            : Continuous straight-line replaced by segmented traces with
                                        connectgaps=False & visible data gap warning.
Stock Conviction Score 0.0 Fix        : Distinguishes legacy placeholder from live canonical score.
                                        Current live stock scores read from canonical V3.2 service.
Entity Field Applicability            : Stock flow/radar clearly marked as 'Not applicable at stock level'.
                                        Industry & sector display genuine canonical metrics.
Rating Markers Redesign               : Overlapping permanent text removed. Replaced by clean circular 
                                        markers with rich unified hover tooltips.
Model-Implied Projections (Read-Only) : 1D, 5D, 20D, 60D canonical horizons + 20D P10-P90 quantiles.
                                        Future dates resolved on actual NSE trading calendar.

Database Row Counts                   : data/market_flow.db     : 182,244 price rows (0 Modified, 0 Deleted)
                                        data/decision_ledger.db : 777,946 decision rows (0 Modified, 0 Deleted)
Full Test Suite Execution             : 208 / 208 PASSED (100% GREEN ✅ in 11.15s)
======================================================================================================
```

---

## 2. Root Cause Diagnostics & Implemented Fixes

### 1. Straight-Line Historical Price Bug (Fixed)
* **Root Cause**: The raw historical decision sessions contain a 314-day gap between `2025-08-22` and `2026-07-02`. Plotly on a continuous calendar axis drew a diagonal connecting line across the missing 10 months.
* **Implemented Fix in [`dashboard/decision_memory.py`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/dashboard/decision_memory.py)**:
  * Automatically detects calendar gaps ($> 10	ext{ days}$).
  * Renders a clear informational notice: `⚠️ Historical Data Gap Notice: A non-contiguous gap of 314 days exists between historical sessions. The chart renders actual historical observations with honest visual separation (no artificial connecting lines).`
  * Splits the price line into separate contiguous segment traces and sets `connectgaps=False`.

### 2. Stock Conviction Score 0.0 for Legacy Snapshots (Fixed)
* **Root Cause**: Phase 30B copied `stock_metrics.leadership_score` which was unpopulated (`0.0`) in the legacy database.
* **Implemented Fix in [`dashboard/decision_memory.py`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/dashboard/decision_memory.py)**:
  * In historical timeline: Displays `"Historical Score: Not Available (Legacy placeholder)"` instead of misleading `0.0`.
  * For current state header: Queries `analytics.canonical_v3_2_service.get_canonical_stock_quant_score()` read-only to show the genuine live V3.2 strength score (e.g. `93.7 / 100 (Canonical V3.2)` for NETWEB).

### 3. Entity-Specific Field Applicability (Fixed)
* **STOCK**: Flow State and Early Radar display `"Not applicable at stock level"`.
* **INDUSTRY**: Displays canonical `score_today`, `flow_state`, `early_radar_score`, `alert_level`, and `breadth_50`.
* **SECTOR**: Displays macro sector `score_today`, `flow_state`, and `breadth_50` without fabricating a stock-style price series.

### 4. Rating Marker Redesign (Fixed)
* Removed permanent overlapping text annotations on every point (`mode="markers"`).
* Distinct color scheme:
  * `STRONG BUY`: `#059669` (Emerald)
  * `BUY`: `#10B981` (Green)
  * `WATCH`: `#3B82F6` (Blue)
  * `NEUTRAL`: `#64748B` (Slate)
  * `REDUCE`: `#F59E0B` (Amber)
  * `AVOID`: `#EF4444` (Red)
* Rich unified hover tooltip exposes: Date, Previous View, New View, Conviction Score, Reference Price, Flow State, and Early Radar.

### 5. Read-Only Canonical Forecast & Model-Implied Projections (New)
* Implemented [`storage/canonical_forecast_service.py`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/storage/canonical_forecast_service.py) reading frozen outputs from [`research/final_v3/results/final_predictions.csv`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/research/final_v3/results/final_predictions.csv).
* **Multi-Horizon Summary**: 1D, 5D, 20D, 60D expected returns.
* **20D Quantile Table**: $P_{10}$ (Bearish Tail), $P_{25}$ (Conservative), $P_{50}$ (Median / Mode), $P_{75}$ (Optimistic), $P_{90}$ (Bullish Tail).
* **Trading-Calendar Date Arithmetic**: $+20	ext{ sessions}$ from $T=	ext{2026-08-24}$ resolves to **2026-09-21** (skipping weekends and exchange holidays).
* **Model-Implied Stock Price Projection**:
  $$	ext{Target Price} = 	ext{Current Price} 	imes (1 + 	ext{Parent Industry Expected Return})$$
  $$	ext{Quantile Band} = \left[ 	ext{Price} 	imes (1 + P_{10}), \; 	ext{Price} 	imes (1 + P_{90}) ight]$$
* Explicit probabilistic disclaimers and visual separation between historical actuals and model-implied future ranges.

---

## 3. Visual QA Results

```text
1. STOCK: NETWEB
   - Historical records: 250 sessions with clean 314-day gap separation (no straight line).
   - Live Canonical V3.2 Score: 93.7 / 100 | Action: STRONG BUY.
   - Flow & Radar: "Not applicable at stock level".

2. STOCK: RELIANCE (Parent Industry: Refining & Marketing)
   - Current Reference Price: ₹1,309.80
   - Model-Implied 20D Projection:
     - 20D Target Date: 2026-09-21 (+20 Trading Sessions)
     - 20D Expected Return: +0.13% (Implied Midpoint: ₹1,311.50)
     - P10 Bearish Tail: -10.23% (Implied: ₹1,175.81)
     - P90 Bullish Tail: +10.49% (Implied: ₹1,447.20)

3. INDUSTRY: Aerospace & Defence
   - Canonical 20D Expected Return: -1.06% | Win Probability: 44.3%
   - 20D Range [P10 - P90]: [-11.4%, +9.3%]
   - Confidence / Risk: 60.5 / 55.7 | Regime: NORMAL

4. SECTOR: Steel
   - Latest Macro Strength Score: 73.1 / 100 | Action: STRONG BUY
   - Strength Trajectory displayed without fake stock price.
```

---

## ============================================================
## PHASE 33B CHANGE CONTROL AUDIT
## ============================================================

```text
Files Modified                        : 2 (dashboard/decision_memory.py, tests/test_phase32_decision_memory_ui.py)
Files Created                         : 1 (storage/canonical_forecast_service.py — Isolated Read-Only Helper)
Existing Production Code Modified     : 0
Model Files Modified                  : 0
Scoring Files Modified                : 0
Pipeline Files Modified               : 0
Database Schema Changes               : 0
Production DB Row Changes             : 0
Decision Ledger Row Changes           : 0
Historical Data Changes               : 0
Tests Passed                          : 208 / 208 (100% GREEN)
```

---

### 🛑 STOP CONDITION SATISFIED

Phase 33B implementation is complete and verified. The Historical Decision Memory interface is updated at `http://localhost:8501`, all 208 tests pass, and zero model/scoring code was modified. I await your next instruction.
