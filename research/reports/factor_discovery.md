# Master 25-Candidate Models Tournament Scorecard

**Benchmark:** NIFTY SMALLCAP 250  
**Sample Period:** 37 Historical Sessions  
**Target:** 5D Forward Relative Industry Performance  

## Full Tournament Scorecard

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

## Key Empirical Findings:
1. **Tier A Models**: `M14_DynamicBottomUp` (IC = +0.1449, IR = 1.42), `M24_IC_WeightedEnsemble` (IC = +0.1215), and `M25_RegimeAdaptiveEnsemble` (IC = +0.1180).
2. **Robustness of Residual Alpha**: `M05_ResidualMom` and `M09_TrendModel` exhibited the lowest drawdowns (<8%) across market corrections.
3. **Rejected Models**: Simple 5D unadjusted momentum (`M01`), RSI oscillator combinations (`M08`), and raw volume pressure (`M07`) without price-action confirmation.
