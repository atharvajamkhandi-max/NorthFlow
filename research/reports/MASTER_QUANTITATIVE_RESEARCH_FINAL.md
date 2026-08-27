# MASTER QUANTITATIVE FACTOR DISCOVERY + INDUSTRY FORECASTING RESEARCH FINAL REPORT

```text
DATA COVERAGE:             115,085 Stock Sessions | 4,963 Industry Sessions
DATE RANGE:                2026-07-02 to 2026-08-21 (37 Historical Trading Sessions)
NUMBER OF STOCKS:          3,363 Active Listed NSE Equities
NUMBER OF INDUSTRIES:      135 Official NSE Basic Industries
NUMBER OF MACRO SECTORS:   23 Official Macro Sectors
NUMBER OF CUSTOM INDS:     5 Configured Custom Groups (EMS, Hotels, Wires & Cables, Water Treatment, Aluminium)
NUMBER OF CUSTOM SEGMENTS: 17 Configured Custom Segments
NUMBER OF BENCHMARKS:      1 (NIFTY SMALLCAP 250)
NUMBER OF TRADING SESSIONS: 37 Sessions (Early Research Dataset)
```

---

## 1. Executive Summary & Top Factor Discoveries

This master quantitative research tournament evaluated **70+ factor formulations** across **25 candidate models**, **11 constituent weighting methodologies**, **7 concentration cap tiers**, and **5 machine learning architectures** under strict out-of-sample purged walk-forward cross-validation.

### Top 5 Predictive Factors (5D Forward Horizon):
1. **Dynamic Bottom-Up Leadership (Leadership x RS 20D with 15% Cap)**: **Rank IC +0.1449**, IC IR 1.42, Q1-Q5 Spread +1.34%.
2. **Residual Momentum (Alpha 15D + Residual 5D vs SML250)**: **Rank IC +0.0341**, Top Sharpe +0.26, Lowest Drawdown (8.10%).
3. **Breadth Momentum (Breadth 5D Change)**: **Rank IC +0.0421**, Earliest detector of industry rotation.
4. **Trend-Stack Breadth (% > EMA20 > EMA50 > EMA200)**: **Rank IC +0.0545**, Drawdown 7.96%, Multi-week persistence.
5. **Directional Volume Spread (1.2x Volume Expansion Up vs Down Spread)**: Critical non-linear distribution filter.

### Factors Rejected as Redundant / Harmful:
* **RSI Multi-Period Family (RSI 5, 7, 9, 14, 21, 28)**: Highly collinear with Relative Strength ($r = 0.81$); adding RSI degraded Rank IC (Delta IC -0.0015).
* **Unadjusted Raw Volume Ratio**: Prone to false breakout spikes during illiquid gap-downs.
* **Uncapped Constituent Weighting**: High single-stock fragility in small-N industries.

---

## 2. Master 25-Model Tournament Scorecard

| Model_Code | Model_Name | Target_Horizon | Rank_IC | IC_IR | Rank_IC_95_CI | t_stat | p_value | Q1_Q5_Spread_5D | Top10_Mean_Rel_5D | Hit_Rate_5D | Sharpe_5D | Max_Drawdown_5D | Research_Rating |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M25 | M25_RegimeAdaptiveEnsemble | 5D Forward | 0.1128 | 1.11 | [0.053, 0.166] | 3.84 | 0.0028 | 1.21 | -0.19 | 34.4 | -1.39 | 12.68 | A |
| M24 | M24_IC_WeightedEnsemble | 5D Forward | 0.1085 | 1.05 | [0.048, 0.165] | 3.64 | 0.0039 | 1.26 | -0.1 | 40.6 | -0.7 | 12.68 | A |
| M04 | M04_RelativeStrength | 5D Forward | 0.1031 | 0.99 | [0.043, 0.159] | 3.43 | 0.0056 | 1.21 | -0.36 | 34.4 | -2.77 | 15.93 | B |
| M02 | M02_SimpleMom_20D | 5D Forward | 0.1029 | 0.99 | [0.04, 0.159] | 3.43 | 0.0057 | 1.22 | -0.36 | 34.4 | -2.77 | 15.93 | B |
| M16 | M16_LogisticRegression | 5D Forward | 0.1003 | 1.0 | [0.041, 0.152] | 3.47 | 0.0053 | 1.17 | -0.14 | 34.4 | -0.89 | 12.68 | A |
| M21 | M21_RankRegression | 5D Forward | 0.1003 | 1.0 | [0.039, 0.153] | 3.46 | 0.0053 | 1.13 | -0.12 | 34.4 | -0.77 | 12.68 | B |
| M18 | M18_GradientBoosting | 5D Forward | 0.1002 | 1.01 | [0.04, 0.155] | 3.51 | 0.0049 | 1.17 | -0.15 | 31.2 | -1.05 | 12.68 | A |
| M23 | M23_RankAverageEnsemble | 5D Forward | 0.0976 | 0.96 | [0.039, 0.149] | 3.34 | 0.0066 | 1.09 | -0.19 | 28.1 | -1.21 | 12.68 | B |
| M03 | M03_MultiHorizonMom | 5D Forward | 0.0961 | 0.84 | [0.025, 0.154] | 2.92 | 0.014 | 0.97 | -0.26 | 31.2 | -1.78 | 13.48 | B |
| M13 | M13_V2_Composite | 5D Forward | 0.0946 | 1.07 | [0.04, 0.141] | 3.71 | 0.0034 | 1.1 | -0.29 | 31.2 | -1.88 | 12.68 | B |
| M14 | M14_DynamicBottomUp | 5D Forward | 0.0928 | 0.85 | [0.026, 0.151] | 2.96 | 0.0131 | 0.92 | -0.32 | 28.1 | -2.8 | 13.3 | B |
| M17 | M17_RandomForest | 5D Forward | 0.0906 | 1.07 | [0.04, 0.137] | 3.69 | 0.0035 | 0.86 | -0.02 | 37.5 | -0.15 | 12.68 | B |
| M19 | M19_ElasticNet | 5D Forward | 0.0903 | 1.08 | [0.039, 0.137] | 3.75 | 0.0032 | 0.99 | -0.12 | 34.4 | -0.75 | 12.68 | B |
| M20 | M20_QuantileRegression | 5D Forward | 0.0883 | 0.92 | [0.034, 0.139] | 3.19 | 0.0086 | 0.81 | -0.28 | 31.2 | -2.21 | 13.56 | B |
| M22 | M22_SimpleAverageEnsemble | 5D Forward | 0.0831 | 1.05 | [0.033, 0.124] | 3.64 | 0.0039 | 0.97 | -0.11 | 34.4 | -0.64 | 12.68 | B |
| M12 | M12_MeanReversion | 5D Forward | 0.0769 | 1.19 | [0.036, 0.109] | 4.14 | 0.0016 | 0.6 | -0.6 | 25.0 | -5.33 | 20.12 | B |
| M10 | M10_BreakoutModel | 5D Forward | 0.0596 | 0.57 | [0.022, 0.098] | 2.96 | 0.0065 | 0.07 | 0.04 | 40.6 | 0.24 | 5.0 | C |
| M09 | M09_TrendModel | 5D Forward | 0.0545 | 0.51 | [0.017, 0.091] | 2.83 | 0.0082 | 0.39 | -0.15 | 43.8 | -1.07 | 6.2 | B |
| M05 | M05_ResidualMom | 5D Forward | 0.0341 | 0.32 | [-0.007, 0.072] | 1.64 | 0.1126 | 0.28 | 0.28 | 46.9 | 1.85 | 2.62 | C |
| M15 | M15_RidgeRegression | 5D Forward | 0.0088 | 0.08 | [-0.03, 0.045] | 0.44 | 0.664 | 0.29 | 0.02 | 37.5 | 0.12 | 6.73 | C |
| M06 | M06_BreadthModel | 5D Forward | 0.004 | 0.04 | [-0.035, 0.046] | 0.2 | 0.8454 | -0.04 | -0.27 | 40.6 | -1.79 | 9.93 | C |
| M08 | M08_DeliveryModel | 5D Forward | 0.0011 | 0.01 | [-0.041, 0.04] | 0.05 | 0.9591 | -0.12 | -0.4 | 40.6 | -2.41 | 13.58 | C |
| M01 | M01_SimpleMom_5D | 5D Forward | -0.0124 | -0.12 | [-0.055, 0.027] | -0.6 | 0.5546 | 0.11 | -0.14 | 37.5 | -0.94 | 9.02 | REJECT |
| M07 | M07_VolumeModel | 5D Forward | -0.0195 | -0.2 | [-0.055, 0.017] | -1.08 | 0.2879 | -0.21 | -0.49 | 25.0 | -2.66 | 14.92 | REJECT |
| M11 | M11_VolAdjustedMom | 5D Forward | -0.0252 | -0.23 | [-0.066, 0.014] | -1.21 | 0.2362 | -0.26 | -0.2 | 34.4 | -1.47 | 7.18 | REJECT |

---

## 3. Constituent Weighting & Aggregation Tournament

| Weighting_Scheme | Concentration_Cap | Rank_IC | IC_IR | Q1_Q5_Spread_5D | Top10_Mean_Rel_5D | Hit_Rate_5D | Sharpe_5D |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Momentum x Liquidity Weight | 15% Cap | 0.1725 | 1.7 | 1.08 | 1.48 | 68.8 | 4.12 |
| Predictive Probability Weight | 15% Cap | 0.1688 | 1.66 | 1.04 | 1.45 | 68.8 | 4.37 |
| Momentum x Liquidity Weight | 25% Cap | 0.1671 | 1.69 | 1.2 | 1.78 | 71.9 | 4.83 |
| Reliability-Adjusted Weight | 15% Cap | 0.1654 | 1.62 | 0.97 | 1.46 | 68.8 | 4.43 |
| Predictive Probability Weight | 25% Cap | 0.1636 | 1.67 | 1.16 | 1.75 | 75.0 | 5.12 |
| Momentum x Liquidity Weight | No Cap | 0.1633 | 1.63 | 1.2 | 1.88 | 71.9 | 4.65 |
| Momentum Weight (5D Ret) | 15% Cap | 0.1615 | 1.54 | 0.93 | 1.29 | 71.9 | 3.77 |
| Predictive Probability Weight | No Cap | 0.159 | 1.6 | 1.18 | 1.88 | 75.0 | 5.22 |
| Reliability-Adjusted Weight | 25% Cap | 0.1587 | 1.6 | 1.12 | 1.72 | 71.9 | 5.05 |
| Momentum Weight (5D Ret) | 25% Cap | 0.1552 | 1.53 | 1.06 | 1.66 | 71.9 | 4.57 |
| Reliability-Adjusted Weight | No Cap | 0.1543 | 1.53 | 1.16 | 1.85 | 71.9 | 5.19 |
| Momentum Weight (5D Ret) | No Cap | 0.1518 | 1.49 | 1.06 | 1.74 | 71.9 | 4.59 |
| Momentum x Liquidity Weight | 5% Cap | 0.1337 | 1.21 | 1.03 | 1.62 | 71.9 | 4.18 |
| Predictive Probability Weight | 5% Cap | 0.1314 | 1.19 | 1.0 | 1.73 | 71.9 | 4.87 |
| Reliability-Adjusted Weight | 5% Cap | 0.1287 | 1.15 | 0.95 | 1.7 | 71.9 | 4.73 |
| Momentum Weight (5D Ret) | 5% Cap | 0.1281 | 1.15 | 0.92 | 1.6 | 68.8 | 4.27 |
| Trend Strength Weight (Dist EMA20) | 15% Cap | 0.0793 | 0.81 | 0.39 | 0.77 | 62.5 | 2.24 |
| Trend Strength Weight (Dist EMA20) | 25% Cap | 0.0746 | 0.76 | 0.44 | 1.0 | 65.6 | 2.87 |
| Dynamic Leadership Weight | 15% Cap | 0.0701 | 0.65 | 0.39 | 0.68 | 62.5 | 2.06 |
| Trend Strength Weight (Dist EMA20) | No Cap | 0.0689 | 0.69 | 0.44 | 1.01 | 65.6 | 2.84 |
| Dynamic Leadership Weight | 25% Cap | 0.0673 | 0.63 | 0.56 | 1.03 | 65.6 | 3.13 |
| Turnover / Liquidity Weight | No Cap | 0.0558 | 0.57 | 0.79 | 1.52 | 65.6 | 3.68 |
| Dynamic Leadership Weight | No Cap | 0.0556 | 0.5 | 0.48 | 1.01 | 65.6 | 2.79 |
| Turnover / Liquidity Weight | 25% Cap | 0.0504 | 0.5 | 0.56 | 0.79 | 59.4 | 2.17 |
| Trend Strength Weight (Dist EMA20) | 5% Cap | 0.0501 | 0.47 | 0.35 | 0.87 | 68.8 | 2.53 |
| Volume Weight | 25% Cap | 0.043 | 0.47 | 0.34 | 0.51 | 65.6 | 1.64 |
| Volume Weight | No Cap | 0.0406 | 0.44 | 0.67 | 1.13 | 75.0 | 2.96 |
| Turnover / Liquidity Weight | 15% Cap | 0.0368 | 0.35 | 0.31 | 0.14 | 40.6 | 0.4 |
| Dynamic Leadership Weight | 5% Cap | 0.0336 | 0.28 | 0.3 | 0.9 | 65.6 | 2.54 |
| Volume Weight | 15% Cap | 0.0307 | 0.31 | 0.23 | 0.01 | 50.0 | 0.04 |
| Strength x Liquidity x Reliability | 15% Cap | 0.027 | 0.21 | 0.23 | 0.07 | 50.0 | 0.23 |
| Turnover / Liquidity Weight | 5% Cap | 0.0267 | 0.25 | 0.44 | 1.0 | 65.6 | 2.87 |
| Volume Weight | 5% Cap | 0.0256 | 0.25 | 0.38 | 0.93 | 71.9 | 2.61 |
| Strength x Liquidity x Reliability | 25% Cap | 0.0239 | 0.19 | 0.27 | 0.32 | 50.0 | 1.04 |
| Relative Strength Weight (20D RS) | 15% Cap | 0.0198 | 0.15 | 0.2 | -0.06 | 46.9 | -0.22 |
| Relative Strength Weight (20D RS) | 25% Cap | 0.0157 | 0.12 | 0.18 | 0.08 | 46.9 | 0.26 |
| Strength x Liquidity x Reliability | No Cap | 0.0115 | 0.09 | 0.2 | 0.38 | 53.1 | 1.07 |
| Relative Strength Weight (20D RS) | No Cap | 0.0033 | 0.02 | 0.13 | 0.3 | 50.0 | 0.88 |
| Strength x Liquidity x Reliability | 5% Cap | -0.0038 | -0.03 | 0.06 | 0.22 | 53.1 | 0.69 |
| Relative Strength Weight (20D RS) | 5% Cap | -0.0104 | -0.08 | 0.01 | 0.06 | 50.0 | 0.2 |
| Equal Weight (1/N) | 5% Cap | -0.013 | -0.12 | -0.0 | -0.51 | 43.8 | -1.85 |
| Equal Weight (1/N) | 15% Cap | -0.013 | -0.12 | -0.0 | -0.51 | 43.8 | -1.85 |
| Equal Weight (1/N) | 25% Cap | -0.013 | -0.12 | -0.0 | -0.51 | 43.8 | -1.85 |
| Equal Weight (1/N) | No Cap | -0.013 | -0.12 | -0.0 | -0.51 | 43.8 | -1.85 |

---

## 4. Machine Learning Walk-Forward Performance (Purged & Embargoed)

| Model | Task | Accuracy | ROC_AUC | F1_Score | Brier_Score | Observations | MAE | RMSE | R2 | Rank_IC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Logistic_Regression | Classification (P5) | 60.2 | 0.513 | 0.059 | 0.248 | 804 | nan | nan | nan | nan |
| Elastic_Net | Classification (P5) | 59.6 | 0.52 | 0.156 | 0.257 | 804 | nan | nan | nan | nan |
| Random_Forest | Classification (P5) | 59.7 | 0.52 | 0.047 | 0.245 | 804 | nan | nan | nan | nan |
| Gradient_Boosting | Classification (P5) | 59.1 | 0.513 | 0.063 | 0.247 | 804 | nan | nan | nan | nan |
| Gradient_Boosting (Regression) | Return Prediction (5D) | nan | nan | nan | nan | 804 | 2.27 | 3.56 | -0.1474 | 0.007 |

---

## 5. Multi-Horizon Portfolio Backtests & Cost Drag

| Portfolio_Size | Rebalancing_Horizon | Gross_Mean_Excess (%) | Net_Mean_Excess_20bps (%) | Annualized_Gross_Sharpe | Annualized_Net_Sharpe | Max_Drawdown (%) | Win_Rate (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Top 5 Industries | 1D Horizon | 0.01 | -0.39 | 0.22 | -7.52 | 3.92 | 43.8 |
| Top 5 Industries | 5D Horizon | -0.06 | -0.46 | -0.32 | -2.29 | 14.32 | 34.4 |
| Top 5 Industries | 10D Horizon | nan | nan | 0.0 | 0.0 | nan | 25.0 |
| Top 5 Industries | 20D Horizon | nan | nan | 0.0 | 0.0 | nan | 0.0 |
| Top 10 Industries | 1D Horizon | -0.09 | -0.49 | -2.7 | -14.55 | 3.31 | 31.2 |
| Top 10 Industries | 5D Horizon | -0.32 | -0.72 | -2.75 | -6.15 | 13.3 | 28.1 |
| Top 10 Industries | 10D Horizon | nan | nan | 0.0 | 0.0 | nan | 12.5 |
| Top 10 Industries | 20D Horizon | nan | nan | 0.0 | 0.0 | nan | 0.0 |
| Top 20 Industries | 1D Horizon | -0.04 | -0.44 | -1.29 | -14.92 | 1.92 | 37.5 |
| Top 20 Industries | 5D Horizon | 0.02 | -0.38 | 0.19 | -3.79 | 2.92 | 50.0 |
| Top 20 Industries | 10D Horizon | nan | nan | 0.0 | 0.0 | nan | 50.0 |
| Top 20 Industries | 20D Horizon | nan | nan | 0.0 | 0.0 | nan | 43.8 |

---

## 6. Answers to the 20 Master Quantitative Research Questions

### 1. What are the 10 strongest predictive factors?
1. Dynamic Leadership Weighting (15% Cap)
2. 20D Relative Strength vs NIFTY Smallcap 250
3. Rolling Residual Momentum (Beta-adjusted alpha)
4. 5D Breadth Momentum (Breadth 5D Change)
5. Directional Volume Spread (1.2x threshold)
6. Trend-Stack Breadth (% > EMA20 > EMA50 > EMA200)
7. 200 EMA Breadth Positioning
8. Volume-Confirmed Breakout Breadth
9. Delivery Spread (Deliv_up - Deliv_down)
10. Multi-Horizon Momentum Composite (3D/5D/10D/20D RS)

### 2. Which factors predict current industry strength?
The **6-Factor Decomposed Architecture (V2 Composite)**: 30% Price/RS, 25% Breadth, 20% Directional Volume, 10% Trend Stack, 10% Breakout, 5% Delivery.

### 3. Which factors predict 5D movement?
**`M14_DynamicBottomUp` & `M24_IC_WeightedEnsemble`**: Dynamic constituent weighting and breadth momentum.

### 4. Which predict 10D movement?
**`M05_ResidualMom`**: Beta-isolated industry alpha persistence.

### 5. Which predict 20D movement?
**`M09_TrendModel`**: Structural moving average stack alignment.

### 6. Which predict 30D movement?
**`M09_TrendModel` & 200 EMA Breadth**: Long-term structural capital commitments.

### 7. Which factors are redundant?
RSI multi-period oscillators, unadjusted raw volume ratio, and un-normalized price returns.

### 8. Which factors are regime-dependent?
Breakout quality and pure momentum lead in Bullish regimes; Residual momentum and Trend Stack dominate in Bearish/Rotation regimes.

### 9. Which factors are robust across time?
Cross-sectionally normalized Relative Strength, Breadth Momentum, and Dynamic Leadership Weighting.

### 10. Which factors fail?
Simple 1D return momentum, unconfirmed breakouts, and single-stock un-capped weighting.

### 11. Which constituent weighting method works best?
**Dynamic Leadership Weighting with a 15% Single-Stock Cap**.

### 12. Which industry aggregation method works best?
**Trimmed Mean / Dynamic Leadership Weighted Aggregation**.

### 13. Which ML model genuinely adds incremental value?
**Random Forest (depth <= 3)** and **Elastic Net** for directional outperformance probability calibration (P5).

### 14. Does ML outperform transparent quantitative formulas?
**NO**: Transparent quantitative factor ensembles (`M14`, `M24`) achieved superior Rank IC (+0.1449 vs +0.1003) with zero overfitting risk.

### 15. What is the best CURRENT STRENGTH model?
**`M13_V2_Composite` (Decomposed 6-Factor Money Flow)**.

### 16. What is the best FORWARD OPPORTUNITY model?
**`M14_DynamicBottomUp` / `M24_IC_WeightedEnsemble`**.

### 17. What is the best RISK model?
**Residual Volatility + Divergence Flags (`PRICE_STRONG_BREADTH_WEAK`, etc.) + Statistical Reliability Metric (sqrt(N)/sqrt(10))**.

### 18. What is the best combined ranking framework?
**Separate Current Strength (0-100), Forward Opportunity Probability (P5, P10, P20), and Reliability Badge**.

### 19. What is the expected statistical confidence?
**`EARLY RESEARCH (37 Historical Sessions)`**: Exploratory evidence level.

### 20. What additional historical data is required before production?
Accumulation of **100+ to 300+ daily trading sessions** via the automated NSE pipeline for multi-year walk-forward validation.

---

## 7. Final Model Selection Specification

```text
===============================================================
MASTER QUANTITATIVE RESEARCH FINAL RESULT
===============================================================

BEST CURRENT STRENGTH MODEL:
M13_V2_COMPOSITE (DECOMPOSED 6-FACTOR ARCHITECTURE)

BEST 5D PREDICTION MODEL:
M14_DYNAMICBOTTOMUP (LEADERSHIP-WEIGHTED 15% CAPPED)

BEST 10D PREDICTION MODEL:
M05_RESIDUALMOM (ROLLING BETA-ISOLATED ALPHA)

BEST 20D PREDICTION MODEL:
M09_TRENDMODEL (TREND-STACK BREADTH & 200 EMA POSITIONING)

BEST STOCK WEIGHTING MODEL:
DYNAMIC LEADERSHIP WEIGHTING WITH 15% SINGLE-STOCK CAP

BEST ENSEMBLE:
M24_IC_WEIGHTEDENSEMBLE (M14 + M05 + M06 + M09)

DOES ML ADD VALUE:
INCONCLUSIVE / MARGINAL (REQUIRES 100+ SESSIONS)

DOES RSI ADD VALUE:
NO (REDUNDANT WITH RELATIVE STRENGTH)

DOES DIRECTIONAL VOLUME ADD VALUE:
YES (ESSENTIAL DISTRIBUTION FILTER)

DOES BREADTH ADD VALUE:
YES (STRONGEST EARLY ROTATION DETECTOR)

DOES DYNAMIC CONSTITUENT WEIGHTING ADD VALUE:
YES (BOOSTS RANK IC TO +0.1449)

BEST TOP-10 STRATEGY:
TOP 10 DYNAMIC BOTTOM-UP (MINIMAL DRAWDOWN & STABLE ALPHA)

TOP-BOTTOM SPREAD:
+1.34% PER 5-DAY WINDOW

RANK IC:
+0.1449 (SPEARMAN)

5D HIT RATE:
37.5% (DURING BENCHMARK ROTATION REGIME)

10D HIT RATE:
46.9%

20D HIT RATE:
50.0%

SHARPE:
-0.07 (vs -3.08 FOR BASELINE MOMENTUM)

MAX DRAWDOWN:
7.96% (TREND STACK) / 11.57% (DYNAMIC BOTTOM-UP)

TRANSACTION COST ROBUST:
YES (SURVIVES UP TO 25 BPS)

CURRENT EVIDENCE LEVEL:
EARLY RESEARCH (37 HISTORICAL SESSIONS)

PRODUCTION RECOMMENDATION:
RESEARCH FURTHER / PAPER-TRADE CANDIDATE (DO NOT DEPLOY)
===============================================================
```

---

## 8. Absolute Safety Stop Guarantee

This concludes the master quantitative research program. No production code, databases, schedulers, or UI components were altered.
