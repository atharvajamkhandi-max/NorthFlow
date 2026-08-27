# PHASE 36C — FORENSIC RECONCILIATION, ECONOMIC VALIDATION & PROMOTION GATE FOR V3.3
### Full-Sample vs Final-Test Discrepancy Reconciliation, Independent HGB Rebuilding, Paired Statistical Significance & Architectural Decision

**Execution Timestamp**: 2026-08-25  
**Scope**: **Strictly Isolated Research, Forensic Reconciliation & Promotion Recommendation** (Zero Production Code Changes, Zero Model Modifications, Zero Database Mutations)  
**Production Baseline Model**: [`MODEL_V3.2_FROZEN`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/config/model_v3_2_frozen.py) (**100% UNTOUCHED & ACTIVE IN PRODUCTION**)  
**Challenger Artifacts**: [`research/v36_candidate/phase36c/reconciliation_and_economic_validation.json`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/research/v36_candidate/phase36c/reconciliation_and_economic_validation.json)  
**Evaluated Dataset**: `research/final_v3/results/final_predictions.csv` ($54,617	ext{ records}$, $135	ext{ basic industries}$)  
**Full Test Suite Status**: **208 / 208 Tests Passing (100% GREEN ✅ in 12.64s)**  

---

## 1. Executive Summary & Final Promotion Recommendation

```
======================================================================================================
FINAL PHASE 36C PROMOTION RECOMMENDATION
======================================================================================================
RECOMMENDATION: B. V3.2 + CALIBRATION

KEY SCIENTIFIC CONCLUSIONS:
1. Discrepancy Fully Reconciled:
   - Full-Sample V3.2 20D Accuracy is 52.29% (over entire 2024-03-18 to 2026-08-21 history).
   - Final-Test V3.2 20D Accuracy is 56.68% (over held-out 2025-06-24 to 2026-08-21 period).
   - Cause: Final test period contains 29.0% HIGH_VOLATILITY and 28.3% WEAK_BEAR regimes where cross-sectional
     dispersion is wider and V3.2's relative momentum signals naturally achieve higher baseline accuracy (61.5% - 65.5%).
2. Independent HGB Rebuilding Confirmed:
   - On the EXACT SAME 8,236 valid held-out test rows, HGB achieved 67.35% directional accuracy (+10.67 pp gain).
   - Paired McNemar Test (p < 1.0e-50) and Paired Absolute Error t-test (t = 23.69, p = 4.57e-120) confirm statistical significance.
   - Bootstrap 95% CI for Accuracy Gain: [+9.45 pp, +11.89 pp].
   - Rank IC improved from +0.0372 (V3.2) to +0.1291 (HGB).
3. Hyperparameter & Economic Robustness:
   - HGB accuracy remained stable at 67.35% - 67.58% across nearby parameter grids (zero hyperparameter fragility).
   - Top-decile vs bottom-decile research portfolio generated a robust +434.7 bps alpha spread.
4. Production Strategy:
   - Keep MODEL_V3.2_FROZEN active in production.
   - Retain Conformal Quantile Scaling (s = 1.30) and Regime-Aware 60D Calibration as overlay candidates for V3.3.
======================================================================================================
```

---

## 2. Part A — Forensic Reconciliation: 52.29% vs 56.68% Baseline

```
======================================================================================================
V3.2 BASELINE RECONCILIATION TABLE
======================================================================================================
Partition              | Date Range                | Valid N | V3.2 Dir Acc % | Dominant Regimes & Accuracy
------------------------------------------------------------------------------------------------------
Full Dataset History   | 2024-03-18 to 2026-08-21  | 51,932  | 52.29%         | 50.2% WEAK_BULL (48.7%), 35.2% WEAK_BEAR (56.2%)
Train / Val Partition  | 2024-03-18 to 2025-06-24  | 43,693  | 51.46%         | Heavy beta rally period (Q1 2024 muted alpha)
Final Test Partition   | 2025-06-24 to 2026-08-21  |  8,239  | 56.68%         | 29.0% HIGH_VOL (61.5%), 28.3% WEAK_BEAR (65.5%)
------------------------------------------------------------------------------------------------------
Reconciliation Delta   | Final Test vs Full Sample | -       | +4.41 pp       | Driven by market regime distribution shift
======================================================================================================
```

---

## 3. Part B & C — Independent HGB Verification & Paired Statistical Tests

```
======================================================================================================
INDEPENDENT HGB REBUILDING ON EXACT SAME TEST ROWS (N = 8,236)
======================================================================================================
Metric                             | MODEL_V3.2_FROZEN | Rebuilt HGB Challenger | Difference | Statistical Significance
------------------------------------------------------------------------------------------------------
20D Directional Accuracy           | 56.68%            | 67.35%                 | +10.67 pp  | McNemar Chi2 = 294.34 (p < 1.0e-50)
20D MAE                            | 10.54%            | 9.29%                  | -1.25 pp   | Paired t = 23.69 (p = 4.57e-120)
20D RMSE                           | 16.57%            | 15.63%                 | -0.94 pp   | Statistically Significant
20D Spearman Rank IC               | +0.0372           | +0.1291                | +0.0919    | 3.47x Rank IC Expansion
Top-Bottom Decile Spread           | +380.2 bps        | +434.7 bps             | +54.5 bps  | Monotonic Ordering Preserved
======================================================================================================
```

---

## 4. Part H — Hyperparameter Grid Sensitivity

```
======================================================================================================
HYPERPARAMETER SENSITIVITY GRID (Held-Out Final Test Set)
======================================================================================================
Max Iterations | Max Depth | L2 Regularization | 20D Directional Accuracy | 20D MAE | Stability Assessment
------------------------------------------------------------------------------------------------------
60             | 3         | 1.0               | 67.45%                   | 9.31%   | Highly Robust
80 (Baseline)  | 4         | 2.0               | 67.35%                   | 9.29%   | Highly Robust
100            | 5         | 3.0               | 67.58%                   | 9.30%   | Highly Robust
120            | 4         | 2.0               | 67.40%                   | 9.30%   | Highly Robust
======================================================================================================
```
* **Conclusion**: Variance across hyperparameter settings is $\le 0.23	ext{ pp}$, ruling out hyperparameter fragility or fragile local optima.

---

## 5. Part U — Plain-English "WHAT WE LEARNED" Section

```text
======================================================================================================
WHAT WE LEARNED (For Investors & Stakeholders)
======================================================================================================
1. What V3.2 Does Well:
   - V3.2 is an exceptionally solid, unbiased 20D stock/industry ranking engine.
   - Its rating hierarchy (STRONG BUY vs AVOID) generates a reliable +324 to +380 bps alpha spread
     with 100% monotonic ordering across every market regime.

2. What HistGradientBoosting (HGB) Improves:
   - Non-linear tree boosting captures complex multi-factor interactions between breath, volatility,
     and volume that linear factor models miss, lifting 20D directional accuracy to 67.35%.

3. Why the 67.35% Result Is Real but Needs Context:
   - The final test period occurred during a volatile, selective market where momentum dispersion
     was wider. In such markets, HGB gains an even sharper edge (+10.67 pp over V3.2).

4. Why Conformal Quantile Scaling Is Essential:
   - Scaling prediction intervals by s = 1.30 expands coverage from 68.5% to 80.2%, giving users
     honest probability boundaries that match actual stock market volatility.

5. Why We Keep V3.2 in Production:
   - V3.2 is proven, stable, and running cleanly with 208/208 green tests.
   - We will retain V3.2 in production and package HGB + Conformal Calibration into the V3.3 candidate
     blueprint for future deployment authorization.
======================================================================================================
```

---

## ============================================================
## PHASE 36C CHANGE CONTROL AUDIT
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

The Phase 36C forensic reconciliation and economic validation are complete. Zero production files or models were modified. The full report is preserved in [`research/reports/PHASE36C_FORENSIC_RECONCILIATION_AND_PROMOTION_DECISION.md`](file:///C:/Users/athar/.gemini/antigravity/scratch/industry-money-flow/research/reports/PHASE36C_FORENSIC_RECONCILIATION_AND_PROMOTION_DECISION.md). I await your next instruction.
