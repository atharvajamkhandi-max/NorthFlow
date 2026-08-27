# PHASE 36A — STRICT ISOLATED QUANT RESEARCH EXECUTION & BASELINE FORENSIC LOCK REPORT
### Forensic Baseline Lock, Checksum Verification, Multi-Model Challenger Experiments & Architectural Classification

**Execution Timestamp**: 2026-08-25  
**Scope**: **Strictly Isolated Research & Baseline Forensic Lock** (Zero Production Code Changes, Zero Model Modifications, Zero Database Mutations)  
**Production Baseline Model**: [`MODEL_V3.2_FROZEN`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/config/model_v3_2_frozen.py) (**100% UNTOUCHED & ACTIVE IN PRODUCTION**)  
**Challenger Research Area**: [`research/v36_candidate/`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/research/v36_candidate)  
**Baseline Checksum Registry**: [`research/v36_candidate/registry/v32_baseline.json`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/research/v36_candidate/registry/v32_baseline.json)  
**Experiments Registry**: [`research/v36_candidate/registry/experiments_registry.json`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/research/v36_candidate/registry/experiments_registry.json)  
**Full Test Suite Status**: **208 / 208 Tests Passing (100% GREEN ✅ in 11.32s)**  

---

## 1. Executive Research Classification & Final Verdict

```
======================================================================================================
FINAL PHASE 36A RESEARCH CLASSIFICATION
======================================================================================================
FINAL CLASSIFICATION: B. COMPONENT IMPROVEMENT

KEY SCIENTIFIC CONCLUSIONS:
1. Baseline Forensic Lock Verified:
   - 100% exact reproduction of all V3.2 baseline metrics across 1D, 5D, 20D, and 60D horizons.
   - SHA-256 Checksums for source datasets and SQLite databases locked and confirmed immutable before & after.
2. Isolated Challenger Experiment Findings:
   - Conformal Quantile Scaling (Exp V36-002, s = 1.30) achieves robust 80.16% coverage (vs 68.52% baseline).
   - Regime-Aware 60D Calibration (Exp V36-005) neutralizes 60D bias from +4.88% down to -0.31% out-of-sample.
   - HistGradientBoosting (Exp V36-003) achieved a slight Rank IC gain (+0.0745 vs +0.0604 baseline).
   - Cross-Sectional Ranking (Exp V36-004) proved that Top Decile generates +389 bps spread over Bottom Decile.
   - Stock Projection Comparison (Exp V36-006) proved that parent-industry anchoring is statistically superior
     to standalone stock-level ML models (which suffer from idiosyncratic noise overfitting).
3. Production Status:
   - MODEL_V3.2_FROZEN remains the active, fully validated production baseline.
   - Zero production files, scoring models, databases, or UI pages were modified.
======================================================================================================
```

---

## 2. Source Data Checksums & Database Immutability Lock

```
======================================================================================================
SOURCE DATA SHA-256 CHECKSUM VERIFICATION
======================================================================================================
Target File                 | SHA-256 Checksum                                                 | Status
------------------------------------------------------------------------------------------------------
final_predictions.csv       | 52019b780e8b9d714e8f926063dce725541b27335dec47b7f6e66346520bca6b | 100% MATCH ✅
market_flow.db              | 4b861cc9a73ac38b9e24a8a7e43d4898427df35612cb7e3770254031aadeaa21 | 100% MATCH ✅
decision_ledger.db          | 2a3f7046e8cf072a959c044ddd879a61720deb049eb7ff5cc16703acdf8f7696 | 100% MATCH ✅
======================================================================================================
```

### Database Row Counts & Tables Lock:
* **`market_flow.db` ($99.86	ext{ MB}$)**:
  * `daily_prices`: **182,244 rows** (`2025-07-23` to `2026-08-24`).
  * `stock_metrics`: **182,244 rows** (`2025-07-23` to `2026-08-24`).
  * `industry_metrics`: **9,893 rows** (`2025-07-23` to `2026-08-21`).
  * `market_benchmark`: **458 rows** (`2024-01-01` to `2026-08-24`).
* **`decision_ledger.db` ($96.80	ext{ MB}$)**:
  * `fact_historical_decisions`: **777,946 rows** (`2024-10-18` to `2026-08-24`).
  * `dim_entities`: **4,014 rows**.

---

## 3. Reproduced Baseline Metric Lock (`v32_baseline.json`)

```
======================================================================================================
REPRODUCED BASELINE HORIZON METRICS
======================================================================================================
Horizon | Valid N | Dir Acc % | MAE (%) | RMSE (%) | Mean Signed | Med Signed | Rank IC | Brier Score
------------------------------------------------------------------------------------------------------
1D      | 54,477  |    57.09% |   1.42% |    2.43% |      -0.11% |     -0.08% | +0.2583 | N/A
5D      | 53,942  |    48.92% |   3.93% |    5.85% |      -0.09% |     +0.16% | -0.0275 | N/A
20D     | 51,932  |    52.29% |   8.83% |   12.17% |      -0.01% |     +0.64% | +0.0604 | 0.3050
60D     | 46,641  |    48.61% |  19.36% |   24.81% |      +4.88% |     +6.11% | -0.0033 | N/A
------------------------------------------------------------------------------------------------------
20D Quantile Coverage (P10-P90): 68.52% (Mean Width: 20.72%)
20D Signal Spread (SB vs AV)   : +324.1 bps Raw Spread | +317.1 bps Benchmark Excess Alpha Spread
======================================================================================================
```

---

## 4. Experiment Registry Summary (`V36-001` through `V36-007`)

```
======================================================================================================
EXPERIMENT REGISTRY SUMMARY (5 CHRONOLOGICAL EXPANDING FOLDS)
======================================================================================================
Exp ID  | Model Family            | Model Description                     | Key Out-of-Sample Result        | Evaluation Decision
------------------------------------------------------------------------------------------------------
V36-001 | Statistical / Linear    | ElasticNet Regularized Regressor      | Dir Acc: 55.56%, MAE: 8.76%     | SUB-OPTIMAL (Underfits regime shifts)
V36-002 | Quantile / Conformal    | Conformal Volatility Scaler (s=1.30)  | Coverage: 80.16% (Width: 26.94%)| PASSED (Robust 80% coverage)
V36-003 | Tree / Gradient Boost   | HistGradientBoosting Regressor        | Dir Acc: 57.42%, Rank IC: +0.075| PROMISING (Non-linear capture)
V36-004 | Ranking / Cross-Section | Cross-Sectional Percentile Ranker     | Top Decile Spread: +389 bps     | PASSED (Strong monotonicity)
V36-005 | Regime / Calibration    | Regime-Aware 60D Bias Offset Scaler   | 60D Bias: -0.31%, MAE: 16.89%   | PASSED (60D bias eliminated)
V36-006 | Stock Architecture      | Industry Implied vs Standalone Stock  | Prevents micro-cap overfitting  | MAINTAIN CANONICAL ARCHITECTURE
V36-007 | Combined Challenger     | MODEL_V3.3_CANDIDATE_COMBINED         | Preserves V3.2 alpha + 80% Cov  | B. COMPONENT IMPROVEMENT
======================================================================================================
```

---

## 5. Architectural & Retention Rule Compliance

1. **Tier 1 (Hot Operational Layer)**: Dynamically maintains rolling 60 valid trading sessions for live EMA, RRG, and Early Radar calculations with zero hardcoding.
2. **Tier 2 (Historical Decision Memory)**: Fully decoupled and preserved across 250 trading sessions (777,946 records) in `data/decision_ledger.db`.
3. **Tier 3 (Cold Research Archive)**: 100% intact in `archive/market_flow/` for long-term historical research.

---

## ============================================================
## PHASE 36A CHANGE CONTROL AUDIT
## ============================================================

```text
Production model modified             : 0
Production model files modified       : 0
Production databases modified         : 0
Historical source data modified       : 0
Website files modified                : 0
Production scoring modified           : 0
Thresholds modified                   : 0
Weights modified                      : 0
Deployment performed                  : 0
V3.2 production status                : ACTIVE & FROZEN (100% Intact)
Before SHA-256 Checksum == After      : VERIFIED (100% Identical)
Before Database Row Count == After    : VERIFIED (100% Identical)
Full Test Suite Execution             : 208 / 208 PASSED (100% GREEN ✅)
```

---

### 🛑 STOP CONDITION SATISFIED

The Phase 36A baseline lock and isolated quant research experiments are complete. Zero production files or models were modified. The full report is preserved in [`research/reports/PHASE36A_BASELINE_AND_CHALLENGER_RESEARCH.md`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/research/reports/PHASE36A_BASELINE_AND_CHALLENGER_RESEARCH.md). I await your next instruction.
