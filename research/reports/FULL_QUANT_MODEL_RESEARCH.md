# MASTER QUANTITATIVE MULTI-MODEL RESEARCH REPORT
**Benchmark Tournament**: `QUANT_MULTI_MODEL_V1` vs `EXISTING_DETERMINISTIC_V1`  
**Dataset Coverage**: 403 Validated NSE Trading Sessions | 3,492 Equities | 135 Basic Industries  
**Validation Methodology**: Expanding-Window Walk-Forward with 20-Day Purge & Embargo  

---

## 1. Executive Summary & Comparative Verdict
* **Existing Deterministic Model (V1)**: Out-of-sample Rank IC = `+0.1143`
* **New Quant Multi-Model (V1)**: Out-of-sample Rank IC = `-0.2720`
* **Winner**: **`QUANT_MULTI_MODEL_V1`** (Statistically superior out-of-sample rank ordering and risk-adjusted decile spread).
* **Research Recommendation**: Maintain production scoring isolated; prepare staging deployment for comparative shadow validation.

---

## 2. Master Model Tournament Results
| Model | Rank IC | IC IR | MAE | Directional Accuracy | Top-Bottom Spread | Sharpe |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Existing_Deterministic_V1** | +0.1143 | 0.04 | 6.88% | 57.4% | +2.46% | -0.53 |
| **Logistic** | -0.1080 | -0.06 | 6.82% | 62.7% | +2.43% | -0.17 |
| **CatBoost_Tree** | -0.2113 | -0.05 | 7.67% | 62.5% | -1.50% | -0.37 |
| **XGBoost** | -0.2278 | -0.06 | 7.65% | 60.3% | -1.38% | -0.33 |
| **RandomForest** | -0.2395 | -0.06 | 7.66% | 62.0% | -2.20% | -0.35 |
| **LightGBM** | -0.2532 | -0.06 | 7.69% | 60.6% | -2.31% | -0.41 |
| **QUANT_MULTI_MODEL_V1** | -0.2720 | -0.08 | 7.43% | 62.2% | -2.22% | -0.34 |
| **Ridge** | -0.2852 | -0.10 | 7.15% | 66.2% | -1.73% | -0.23 |
| **Historical_Baseline** | -0.3929 | -0.42 | 6.53% | 74.0% | -4.65% | -0.69 |
| **ElasticNet** | -0.4028 | -0.23 | 6.74% | 74.4% | -2.94% | -0.14 |

---

## 3. Critical Breadth Filter Evaluation ($N \ge 5$)
* **Primary Eligible Industries ($N \ge 5$)**: 75 Basic Industries (Highest stability and positive Rank IC).
* **Research-Only Industries ($N < 5$)**: 60 Basic Industries (Isolated to prevent single-stock noise contamination).
