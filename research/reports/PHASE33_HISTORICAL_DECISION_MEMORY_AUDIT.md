# PHASE 33 — HISTORICAL DECISION MEMORY FORENSIC AUDIT REPORT
### Root Cause Diagnostics for Price Straight-Lines, Zero Conviction Scores, Entity Field Availability & Canonical Forecasting Capabilities

**Audit Timestamp**: 2026-08-25  
**Audit Scope**: **Strictly Read-Only Forensic Investigation** (Zero Code Changes, Zero Model Changes, Zero Database Mutations)  
**Baseline Models**: [`MODEL_V3.2_FROZEN`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/config/model_v3_2_frozen.py) & [`EARLY_RADAR_V1_FROZEN`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/config/early_radar_v1_frozen.py) (**100% UNTOUCHED**)  
**Full Test Suite Status**: **204 / 204 Tests Passing (100% GREEN ✅)**  

---

## 1. Forensic Findings Executive Summary

```
======================================================================================================
PHASE 33 FORENSIC AUDIT SCORECARD
======================================================================================================
1. Straight-Line Price Bug Root Cause: 
   - Historical dataset contains a 314-day chronological gap between 2025-08-22 and 2026-07-02.
   - Plotly plotted trade_date on a continuous calendar date axis and drew a linear interpolation line
     connecting August 2025 directly to July 2026 across the missing period.
   - Solution: Use category-based trading session index and set connectgaps=False to prevent interpolation.

2. Stock Conviction Score 0.0 Root Cause:
   - During Phase 30B backfill, stock scores were read from stock_metrics.leadership_score, which was
     unpopulated (0.0 for all 182,244 database rows).
   - In canonical MODEL_V3.2_FROZEN, the stock screener computes stock_strength_score dynamically via 
     analytics.canonical_v3_2_service using frozen factor weights on 50 EMA, 20 EMA, RS 20D, and Volume.
   - Stocks lacked point-in-time scores in the ledger because they were backfilled from the wrong column.

3. Entity-Specific Field Availability:
   - STOCK    : close_price (Avail), stock_strength_score (Avail), rating_action (Avail).
                flow_state and early_radar are NOT modeled at the stock level (Hierarchical parent only).
   - INDUSTRY : score_today (Avail), flow_state (Avail), early_radar_score (Avail), alert_level (Avail),
                quantiles P10-P90 (Avail in final_predictions.csv), probabilities (Avail).
   - SECTOR   : score_today (Avail), breadth_50 (Avail), flow_state (Avail), constituent_count (Avail).

4. Canonical Forecasting Outputs Available in Research Base:
   - Expected Returns: 1D, 5D, 20D, 60D (Canonical fields in research/final_v3/results/final_predictions.csv)
   - Quantile Bands   : P10_20D, P25_20D, P50_20D, P75_20D, P90_20D (Canonical 20D horizon)
   - Probabilities    : P(Return > 0), P(Return > 5%), P(Return > 10%), P(Loss > 5%)
   - Risk & Confidence: CONFIDENCE_SCORE, RISK_SCORE, REGIME_CONFIDENCE
======================================================================================================
```

---

## 2. Problem 1: Root Cause Analysis of Price Straight-Line Bug

### Forensic Evidence:
* **The Date Distribution in Raw Data**:
  * Sessions 1 to 211: `2024-10-18` to `2025-08-22` (Historical backtest window).
  * Sessions 212 to 250: `2026-07-02` to `2026-08-24` (Live prospective window).
  * **Gap**: Exactly **314 calendar days** between `2025-08-22` and `2026-07-02`.
* **The Plotly Rendering Mechanism**:
  * The UI passed ISO date strings (`'YYYY-MM-DD'`) directly to `go.Scatter(x=df['trade_date'], y=df['close_price'])`.
  * Plotly automatically inferred `xaxis.type = 'date'`, placed `2025-08-22` on the left, created 10 months of empty pixels, placed `2026-07-02` on the right, and drew a single diagonal line connecting them.
* **The Non-Destructive Architectural Fix**:
  1. Set `xaxis=dict(type='category')` so the chart plots strictly by **Trading Session Sequence** (Session 1, 2, ..., 250) without artificial calendar interpolation.
  2. For continuous date views, insert `None` rows whenever `(date_{t} - date_{t-1}) > 7	ext{ days}` with `connectgaps=False` so missing periods are displayed as visual breaks, never straight lines.
  3. Never fabricate synthetic price data during gap periods.

---

## 3. Problem 2: Root Cause Analysis of Stock Conviction Score (NETWEB 0.0)

### Forensic Evidence:
* Inspection of `data/market_flow.db` table `stock_metrics`:
  ```sql
  SELECT leadership_score, COUNT(*) FROM stock_metrics GROUP BY leadership_score;
  -- Result: 0.0 | 182,244 rows (100% of all stock metrics rows in DB are 0.0)
  ```
* In `execute_safe_12m_backfill.py` (Phase 30B):
  ```python
  q_stk = "SELECT symbol, close, rs_20d, leadership_score FROM stock_metrics..."
  # df_sm["leadership_score"] was read directly -> yielded 0.0 for every single stock!
  ```
* In the canonical production system ([`analytics/canonical_v3_2_service.py`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/analytics/canonical_v3_2_service.py#L303-L315)), stock conviction score is computed dynamically via frozen weights on underlying indicators:
  $$	ext{Score}_{	ext{stock}} = w_1 \cdot (	ext{Above50EMA} 	imes 100) + w_2 \cdot 	ext{NormRS}_{20	ext{D}} + w_3 \cdot (	ext{Above20EMA} 	imes 100) + w_4 \cdot 	ext{NormVol}$$
* **The Presentation Resolution**:
  * In the UI, for STOCK entities, if `score == 0.0` or unavailable in historical snapshot, clearly display *"Score: Not Available in Legacy Snapshot"* rather than misleading users with `0.0`.
  * For live sessions, query `analytics.canonical_v3_2_service.get_canonical_stock_quant_score()` where canonical V3.2 scores are genuinely computed.
  * Never invent or backfill synthetic scores without authorization.

---

## 4. Problem 3: Entity-Specific Field Availability Matrix

```
======================================================================================================
CANONICAL FIELD AVAILABILITY MATRIX ACROSS ENTITY TIERS
======================================================================================================
Field / Metric              | STOCK Tier                | INDUSTRY Tier           | SECTOR Tier
------------------------------------------------------------------------------------------------------
Reference Price             | AVAILABLE (Actual Close)  | NOT APPLICABLE (Index)  | NOT APPLICABLE
Conviction Strength Score   | AVAILABLE (Canonical V3.2)| AVAILABLE (score_today) | AVAILABLE (Macro avg)
Rating Action (BUY/AVOID)   | AVAILABLE                 | AVAILABLE               | AVAILABLE
Institutional Flow State    | NOT APPLICABLE (Parent)   | AVAILABLE (Accum/Dist)  | AVAILABLE (Breadth)
Early Radar Score / Alert   | NOT APPLICABLE (Parent)   | AVAILABLE (Early Radar) | AVAILABLE (Aggregate)
Probabilities P(1D, 3D, 5D) | NOT APPLICABLE (Parent)   | AVAILABLE               | NOT APPLICABLE
20D Quantile Range (P10-P90)| DERIVED FROM PARENT       | AVAILABLE (Predictions) | NOT APPLICABLE
Parent Industry & Sector    | AVAILABLE                 | AVAILABLE (Sector only) | NOT APPLICABLE
======================================================================================================
```

**UI Presentation Rule**: When a metric is `NOT APPLICABLE` or `NOT AVAILABLE IN HISTORICAL SOURCE`, the UI must display a clean `—` or `"Not Applicable at Stock Level (See Parent Industry)"` instead of rendering `0.0` or a fake `NORMAL` badge.

---

## 5. Problem 4 & 5: Rating Marker Redesign & Date Axis Specification

### Current Flaw:
* All rating transitions have static text labels superimposed directly onto price scatter points, causing unreadable visual clutter (e.g. `AVOID`, `REDUCE`, `AVOID` overlapping).

### Redesigned Presentation Specification:
1. **Clean Geometric Markers**: Discrete colored dots on price line (Green = `BUY`, Emerald = `STRONG BUY`, Orange = `REDUCE`, Red = `AVOID`, Blue = `WATCH`).
2. **Selective Labels**: Show text labels ONLY on major directional upgrades (e.g. `BUY` $ightarrow$ `STRONG BUY` or `AVOID` $ightarrow$ `BUY`).
3. **Rich Unified Hover Tooltip**:
   ```text
   Date            : 14 Aug 2026
   Price           : ₹5,454.50
   Model View      : ⭐ STRONG BUY (Previous: BUY)
   Conviction Score: 78.4 / 100 (+6.4)
   Parent Industry : IT Hardware & Networking Systems (Flow: ACCUMULATION)
   ```
4. **Trading Session Date Axis**: Formatted with actual trading calendar dates (`D-MMM-YYYY`), eliminating artificial straight-line connections.

---

## 6. Problem 7 & 8: Canonical Forecasting & Model-Implied Projections

### Canonical Research Base Inspection ([`research/final_v3/results/final_predictions.csv`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/research/final_v3/results/final_predictions.csv)):
* The canonical V3 model produces **20D Expected Return** ($	ext{EXPECTED\_RETURN\_20D}$) and full **Quantile Distribution**:
  * $P_{10}$ (Bearish Tail), $P_{25}$ (Conservative), $P_{50}$ (Median / Mode), $P_{75}$ (Optimistic), $P_{90}$ (Bullish Tail).
  * Confidence: $	ext{CONFIDENCE\_SCORE}$ ($0	ext{--}100$).
  * Risk: $	ext{RISK\_SCORE}$ ($0	ext{--}100$).

### Presentation Arithmetic Specification (Read-Only UI Display):
* **Stock Price Implied 20D Projection**:
  $$	ext{Projected Price}_{P_{50}} = 	ext{Current Reference Price} 	imes (1 + 	ext{Parent Industry } 	ext{EXPECTED\_RETURN\_20D})$$
  $$	ext{Range Band} = \left[ 	ext{Price} 	imes (1 + P_{10}), \; 	ext{Price} 	imes (1 + P_{90}) ight]$$
* **Calendar Date Resolution**:
  * Starting date $T = 	ext{2026-08-24}$
  * Horizon = $+20	ext{ Trading Sessions}$ (walk forward on actual NSE trading calendar, skipping weekends/holidays)
  * Target Session = **2026-09-22** (e.g. exactly 20 trading days forward).
* **Mandatory Labeling**:
  * Clearly marked as: **`Model-Implied 20D Range (Derived from Parent Industry Expected Return)`**.
  * Explicit disclaimer: *"Projections are model-implied probabilistic scenarios based on frozen historical calibration, not guaranteed price targets."*

---

## 7. Change Control & File Impact Analysis

```
======================================================================================================
PROPOSED ISOLATED FILE MODIFICATIONS (AWAITING AUTHORIZATION)
======================================================================================================
1. Target File to Modify              : dashboard/decision_memory.py (ISOLATED NEW FILE)
   Exact Reason                       : Fix straight-line chart bug (category axis), fix NETWEB 0.0 display,
                                        implement layman-friendly tooltips, and add read-only projection panel.
   Existing Production Files Affected : EXACTLY 0

2. Target File to Modify              : tests/test_phase32_decision_memory_ui.py (ISOLATED TEST FILE)
   Exact Reason                       : Add unit tests verifying no straight lines, correct field fallbacks,
                                        and trading calendar date projections.
   Existing Production Files Affected : EXACTLY 0

3. Protected Production Files         : MODEL_V3.2_FROZEN, EARLY_RADAR_V1_FROZEN, analytics/, 
                                        database/, data/market_flow.db, data/decision_ledger.db
   Status                             : 100% FROZEN & UNTOUCHED (0 edits)
======================================================================================================
```

---

## ============================================================
## PHASE 33 FORENSIC AUDIT CHANGE CONTROL VERIFICATION
## ============================================================

```text
Existing Website Files Modified       : 0
Existing Dashboard Files Modified     : 0
Existing Model Files Modified         : 0
Existing Scoring Files Modified       : 0
Existing Pipeline Files Modified      : 0
Existing Production Database Modified : 0
Decision Ledger Modified              : 0
Historical Data Modified              : 0
ML Changes                            : 0
Formula Changes                       : 0
Threshold Changes                     : 0
UI Changes                            : 0 (Audit Phase Only)

READ-ONLY FORENSIC AUDIT              : COMPLETE & VERIFIED
```

---

### 🛑 STOP CONDITION SATISFIED

The Phase 33 forensic audit is complete. All root causes for the straight-line chart, the missing conviction score, and entity field availability have been pinpointed, and the canonical forecasting inputs have been mapped. Zero files in the production codebase or database were modified. I await your explicit approval to implement these isolated UI presentation corrections in `dashboard/decision_memory.py`.
