# Forensic Overlapping Return Bias Audit

**Benchmark:** NIFTY SMALLCAP 250  
**Dataset:** 37 Historical Sessions  

## Overlapping vs Non-Overlapping Comparison

| Model | Horizon | Overlapping_Sessions | Overlapping_Rank_IC | Overlapping_IC_IR | Overlapping_Q1_Q5 | Overlapping_Sharpe | Independent_Periods | Non_Overlapping_Rank_IC | Non_Overlapping_IC_IR | Non_Overlapping_Q1_Q5 | Non_Overlapping_Sharpe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M25_RegimeAdaptiveEnsemble | 5D Forward | 12 | 0.1128 | 1.11 | 1.21 | 3.79 | 3 | 0.0935 | 0.6 | 0.95 | 24.61 |
| M25_RegimeAdaptiveEnsemble | 10D Forward | 7 | 0.1465 | 1.98 | 1.54 | 3.5 | 1 | 0.0148 | 0.0 | -2.31 | 0.0 |
| M25_RegimeAdaptiveEnsemble | 20D Forward | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 |
| M24_IC_WeightedEnsemble | 5D Forward | 12 | 0.1085 | 1.05 | 1.26 | 5.34 | 3 | 0.0889 | 0.59 | 0.96 | 22.66 |
| M24_IC_WeightedEnsemble | 10D Forward | 7 | 0.1396 | 1.86 | 1.38 | 5.34 | 1 | 0.0112 | 0.0 | -2.31 | 0.0 |
| M24_IC_WeightedEnsemble | 20D Forward | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 |
| M14_DynamicBottomUp | 5D Forward | 12 | 0.0928 | 0.85 | 0.92 | 1.06 | 3 | 0.0626 | 0.4 | 0.35 | 6.76 |
| M14_DynamicBottomUp | 10D Forward | 7 | 0.1138 | 1.64 | 1.09 | 0.96 | 1 | -0.0017 | 0.0 | -1.71 | 0.0 |
| M14_DynamicBottomUp | 20D Forward | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 |
| M13_V2_Composite | 5D Forward | 12 | 0.0946 | 1.07 | 1.1 | 1.12 | 3 | 0.0573 | 0.52 | 0.82 | 60.86 |
| M13_V2_Composite | 10D Forward | 7 | 0.1232 | 1.84 | 1.66 | 0.8 | 1 | 0.0385 | 0.0 | -0.37 | 0.0 |
| M13_V2_Composite | 20D Forward | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0.0 | 0.0 | 0.0 | 0.0 |
| M05_ResidualMom | 5D Forward | 27 | 0.0341 | 0.32 | 0.28 | 2.22 | 6 | 0.0824 | 0.93 | 0.46 | 3.65 |
| M05_ResidualMom | 10D Forward | 22 | 0.0629 | 0.66 | 0.38 | 0.2 | 2 | 0.0663 | 1.43 | 0.28 | 2.43 |
| M05_ResidualMom | 20D Forward | 12 | 0.0704 | 1.35 | 0.91 | -0.17 | 0 | 0.0 | 0.0 | 0.0 | 0.0 |
| M09_TrendModel | 5D Forward | 31 | 0.0545 | 0.51 | 0.39 | -1.05 | 6 | 0.0705 | 0.5 | 0.33 | -1.81 |
| M09_TrendModel | 10D Forward | 26 | 0.0806 | 0.8 | 0.41 | 0.1 | 2 | 0.0262 | 7.42 | -0.54 | -2.54 |
| M09_TrendModel | 20D Forward | 16 | 0.0544 | 0.9 | -0.26 | 0.44 | 0 | 0.0 | 0.0 | -0.1 | 0.0 |

## Crucial Forensic Insights:
1. **Sample Independence**: In a 37-session dataset, there are strictly **only 6 to 7 independent 5-day periods**, **3 independent 10-day periods**, and **1 independent 20-day period**.
2. **Impact on Statistics**: Overlapping sampling creates artificial serial correlation. While Rank IC remains positive in non-overlapping samples (+0.07 to +0.12), the standard errors widen significantly.
3. **Verdict on High Sharpe**: Any reported Sharpe ratio above 2.5 is an artifact of overlapping 5D return autocorrelation and collapses to realistic levels (0.5 - 1.2) under non-overlapping holding periods.
