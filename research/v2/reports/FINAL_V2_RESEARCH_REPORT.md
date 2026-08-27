# MASTER INSTITUTIONAL V2 QUANTITATIVE RESEARCH THESIS & REPORT
**Namespace**: `research/v2/` (Strictly Isolated Research Environment)  
**Dataset**: 403 Validated NSE Trading Sessions | 3,492 Equities | 135 Basic Industries  
**Validation Methodology**: Chronological Expanding Walk-Forward with 20-Day Purge & Embargo  

---

## 1. Executive Summary & Core Results
* **Champion Model (`Existing_Deterministic_V1`)**: Out-of-Sample Rank IC = `+0.0991` | Decile Spread = `+2.53%`
* **V2 Challenger Tournament (15 Models)**: Evaluated across Linear, Trees, GBDT, Pairwise Rankers, Quantile, and Ensembles.
* **Final Verdict**: **`KEEP_EXISTING_CHAMPION`**
* **Quantitative Rationale**: While V2 formalized multi-horizon expected returns, residualized targets ($\epsilon_i$), and block bootstrap bounds, the Existing Deterministic Champion retains the highest out-of-sample Rank IC and lowest complexity penalty.

---

## 2. 15-Model Tournament Scorecard
| Model | Rank IC | IC IR | MAE | Directional Accuracy | Top-Bottom Spread | Model Quality Score | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Existing_Deterministic_V1** | +0.0991 | 0.03 | 6.81% | 58.4% | +2.53% | 60.8 | **CHAMPION** |
| **V2_OPTIMIZED_ENSEMBLE** | -0.0832 | -0.06 | 6.81% | 65.7% | -1.98% | 0.0 | **BENCHMARK** |
| **Logistic** | -0.1147 | -0.06 | 6.74% | 64.7% | +1.40% | 4.2 | **BENCHMARK** |
| **LambdaRank_Fast** | -0.1484 | -0.05 | 8.55% | 37.0% | +0.22% | 0.0 | **BENCHMARK** |
| **Pairwise_Rank_Regressor** | -0.1493 | -0.07 | 8.13% | 36.8% | +1.07% | 0.0 | **BENCHMARK** |
| **XGBoost** | -0.2518 | -0.07 | 7.48% | 62.6% | -2.30% | 0.0 | **BENCHMARK** |
| **CatBoost_Tree** | -0.2530 | -0.06 | 7.55% | 64.9% | -0.56% | 0.0 | **BENCHMARK** |
| **LightGBM** | -0.2751 | -0.07 | 7.45% | 64.4% | -2.87% | 0.0 | **BENCHMARK** |
| **RandomForest** | -0.2778 | -0.07 | 7.46% | 63.9% | -1.43% | 0.0 | **BENCHMARK** |
| **Huber_Regression** | -0.2857 | -0.10 | 7.15% | 68.8% | -2.33% | 0.0 | **BENCHMARK** |
| **Quantile_Regressor_P50** | -0.2935 | -0.09 | 7.23% | 67.7% | -3.63% | 0.0 | **BENCHMARK** |
| **Ridge** | -0.2972 | -0.11 | 7.17% | 67.5% | -2.37% | 0.0 | **BENCHMARK** |
| **Huber_Loss_Boosting** | -0.3008 | -0.09 | 7.35% | 65.1% | -4.06% | 0.0 | **BENCHMARK** |
| **ExtraTrees** | -0.3701 | -0.12 | 7.17% | 69.0% | -4.29% | 0.0 | **BENCHMARK** |
| **ElasticNet** | -0.4065 | -0.23 | 6.77% | 74.4% | -3.13% | 0.0 | **BENCHMARK** |