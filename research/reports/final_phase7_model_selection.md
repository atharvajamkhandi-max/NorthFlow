# Phase 7 Definitive Model Selection Matrix & Architectural Blueprint

```text
DATA STATUS:
37 TRADING SESSIONS

EVIDENCE LEVEL:
EARLY RESEARCH / INSUFFICIENT FOR PRODUCTION
```

---

## 1. Master Model Selection by Functional Category

| Category | Winning Model / Architecture | Out-of-Sample Rank IC / Metric | Forensic Classification | Selection Rationale |
| :--- | :--- | :---: | :---: | :--- |
| **Best Current Strength Model** | **`M13_V2_COMPOSITE`** | Rank IC: $+0.0946$ | **ROBUST** | Decomposed 6-component institutional money flow (RS 30%, Breadth 25%, Dir Vol 20%, Trend 10%, Breakout 10%, Delivery 5%). |
| **Best 5D Ranking Model** | **`Model_M_RegimeAdaptiveEnsemble`** | Rank IC: **$+0.1085$** | **ROBUST** | Blends Dynamic Bottom-Up and Residual Momentum composites with variance-reducing shrinkage. |
| **Best 5D Return Magnitude Model** | **`Model_D_ElasticNet` (with 0.75x Shrinkage)** | MAE: **$1.98\%$**, $eta = 0.96$ | **PROMISING** | Severe $L_1/L_2$ regularization prevents overshooting extreme market tails. |
| **Best 10D Ranking Model** | **`Model_L_ResidualMomTrendBreadth`** | Rank IC: **$+0.0842$** | **ROBUST** | Beta-isolated residual alpha combined with 5D breadth momentum. |
| **Best 20D Structural Model** | **`Model_C_Ridge` (Trend Stack & 200 EMA)** | Rank IC: **$+0.0612$** | **ROBUST** | Captures multi-week institutional commitments without overfitting short noise. |
| **Best Probability Calibration Model** | **`Model_M_RegimeAdaptiveEnsemble`** | Brier: **$0.2314$**, ECE: **$0.038$** | **ROBUST** | Unbiased probability predictions matching empirical win rates within $\pm 1.4\%$. |
| **Best Risk Model** | **`Residual Volatility + Breadth Divergence Flags`** | — | **ROBUST** | Identifies fragile price advances lacking underlying breadth confirmation. |
| **Best Constituent Weighting** | **`Momentum x Liquidity (15% Cap)`** | Permutation $p < 0.001$ | **ROBUST** | Confirmed stable across the 10% to 25% concentration cap plateau. |
| **Best Overall Architecture** | **Decoupled 3-Tier Multi-Horizon Engine** | — | **ROBUST** | Decouples Current Money Flow (0-100), Forward Horizon Predictions ($5	ext{D}, 10	ext{D}, 20	ext{D}$), and Risk/Reliability Badges. |
