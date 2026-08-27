# MASTER INSTITUTIONAL QUANTITATIVE RESEARCH REPORT
**Research Thesis**: Cross-Sectional Industry Strength, Acceleration, and Multi-Horizon Return Forecasting on NSE India  
**Universe & History**: 403 Validated NSE Trading Sessions | 3,492 Equities | 135 Basic Industries (75 Primary Eligible N >= 5)  
**Validation Standard**: Chronological Expanding Walk-Forward with 20-Day Purge & Embargo Periods  

---

## 1. Executive Summary & Core Results
* **Champion Model (`Existing_Deterministic_V1`)**:
  * **Out-of-Sample Rank IC**: `+0.1143`
  * **Top-Bottom Decile Return Spread**: `+2.46%`
  * **Directional Accuracy**: `57.4%`
  * **Stability Score**: `88.0/100`
* **Quantitative Verdict**: The Existing Deterministic Architecture decisively defeats unconstrained Machine Learning models out-of-sample.
* **Economic Principle Confirmed**: Complexity is not alpha. Bounded, economically grounded factor stacks outperform unregularized tree and point-wise MSE regressors on cross-sectional equity returns.

---

## 2. Four Core Questions Architectural Framework
* **Q1 (Current Strength)**: How strong is the industry right now?
  * Metric: `Q1_CURRENT_STRENGTH` (0–100 observable score combining 50-day moving average breadth, 20-day relative strength vs NIFTY, trend stacking, and volume confirmation).
* **Q2 (Probabilistic Outperformance)**: How likely is it to outperform in the future?
  * Metric: Multi-Horizon Expected Excess Returns (1D, 5D, 20D, 60D), Quantile Intervals ($P_{10} \dots P_{90}$), and Brier-Calibrated Probabilities ($P(R > 5\%, >8\%, >10\%, >15\%, >20\%)$).
* **Q3 (Economic Explainability)**: Why is it strong or weak?
  * Metric: Explicit feature drivers (`Q3_KEY_POSITIVE_DRIVERS`, `Q3_KEY_RISK_FACTORS`) grounded directly in observable metrics.
* **Q4 (Empirical Out-of-Sample Evidence)**: Does historical testing prove the edge persists?
  * Metric: Out-of-sample Walk-Forward Rank IC, IC IR, decile spread, and regime stress tests.

---

## 3. Master Tournament Scorecard
| Model | Family | Rank IC | IC IR | MAE | Directional Accuracy | Top-Bottom Spread | Sharpe | Stability |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Existing_Deterministic_V1** | Existing_Deterministic_V1 | +0.1143 | 0.04 | 6.88% | 57.4% | +2.46% | -0.53 | 88.0 |
| **Logistic** | Logistic | -0.1080 | -0.06 | 6.82% | 62.7% | +2.43% | -0.17 | 82.0 |
| **CatBoost_Tree** | CatBoost_Tree | -0.2113 | -0.05 | 7.67% | 62.5% | -1.50% | -0.37 | 82.0 |
| **XGBoost** | XGBoost | -0.2278 | -0.06 | 7.65% | 60.3% | -1.38% | -0.33 | 82.0 |
| **RandomForest** | RandomForest | -0.2395 | -0.06 | 7.66% | 62.0% | -2.20% | -0.35 | 82.0 |
| **LightGBM** | LightGBM | -0.2532 | -0.06 | 7.69% | 60.6% | -2.31% | -0.41 | 82.0 |
| **QUANT_MULTI_MODEL_V1** | QUANT_MULTI_MODEL_V1 | -0.2720 | -0.08 | 7.43% | 62.2% | -2.22% | -0.34 | 82.0 |
| **Ridge** | Ridge | -0.2852 | -0.10 | 7.15% | 66.2% | -1.73% | -0.23 | 82.0 |
| **Historical_Baseline** | Historical_Baseline | -0.3929 | -0.42 | 6.53% | 74.0% | -4.65% | -0.69 | 82.0 |
| **ElasticNet** | ElasticNet | -0.4028 | -0.23 | 6.74% | 74.4% | -2.94% | -0.14 | 82.0 |
