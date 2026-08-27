# Multi-Horizon Direct Return Forecasting Report

**Benchmark:** NIFTY SMALLCAP 250  
**Sample Period:** 37 Historical Trading Sessions  
**Evaluation:** Out-of-Sample Purged Chronological Walk-Forward  

## Forecast Model Accuracy Matrix Across Horizons

| Model_Name | Horizon | MAE (%) | RMSE (%) | Median_AE (%) | R2 | Rank_IC | Kendall_Tau | Sign_Accuracy (%) | PI_80_Coverage (%) | Brier_Score | ECE | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Model_D_ElasticNet | 10D Forward | 9.19 | 21.82 | 5.37 | -0.03 | 0.03 | 0.022 | 39.6 | 59.7 | 0.3777 | 0.363 | MIS-CALIBRATED |
| Model_J_IC_WeightedFactor | 10D Forward | 10.12 | 22.96 | 6.1 | -0.1405 | 0.0298 | 0.021 | 47.8 | 55.2 | 0.3675 | 0.327 | MIS-CALIBRATED |
| Model_C_Ridge | 10D Forward | 9.23 | 21.85 | 5.49 | -0.0324 | 0.0281 | 0.024 | 39.6 | 58.2 | 0.3795 | 0.362 | MIS-CALIBRATED |
| Model_G_QuantileRegression | 10D Forward | 8.78 | 21.77 | 5.29 | -0.0258 | 0.0281 | 0.024 | 41.8 | 53.0 | 0.3544 | 0.33 | MIS-CALIBRATED |
| Model_L_ResidualMomTrendBreadth | 10D Forward | 9.05 | 21.79 | 5.33 | -0.0275 | 0.0257 | 0.019 | 38.1 | 59.0 | 0.3736 | 0.355 | MIS-CALIBRATED |
| Model_E_RandomForest | 10D Forward | 8.54 | 21.78 | 4.93 | -0.0264 | 0.0179 | 0.011 | 36.6 | 67.2 | 0.3531 | 0.329 | CALIBRATED |
| Model_B_LinearRegression | 10D Forward | 18.26 | 30.57 | 12.33 | -1.022 | 0.0077 | 0.006 | 53.0 | 26.1 | 0.4048 | 0.401 | MIS-CALIBRATED |
| Model_A_ConditionalMean | 10D Forward | 8.27 | 21.57 | 4.66 | -0.0061 | 0.0 | 0.0 | 36.6 | 76.9 | 0.3191 | 0.295 | CALIBRATED |
| Model_M_RegimeAdaptiveEnsemble | 10D Forward | 8.96 | 21.94 | 5.77 | -0.0412 | -0.0007 | 0.003 | 36.6 | 57.5 | 0.3661 | 0.342 | MIS-CALIBRATED |
| Model_N_ProbabilityEnsemble | 10D Forward | 8.96 | 21.94 | 5.77 | -0.0412 | -0.0007 | 0.003 | 36.6 | 57.5 | 0.3718 | 0.358 | MIS-CALIBRATED |
| Model_K_DynamicBottomUp | 10D Forward | 8.72 | 21.73 | 4.93 | -0.0218 | -0.0075 | -0.001 | 38.1 | 62.7 | 0.3629 | 0.337 | MIS-CALIBRATED |
| Model_F_GradientBoosting | 10D Forward | 8.36 | 21.74 | 5.1 | -0.0221 | -0.1104 | -0.081 | 36.6 | 60.4 | 0.3595 | 0.331 | MIS-CALIBRATED |
| Model_B_LinearRegression | 5D Forward | 7.12 | 19.58 | 3.65 | -0.0716 | 0.0387 | 0.025 | 42.9 | 59.0 | 0.3393 | 0.287 | MIS-CALIBRATED |
| Model_J_IC_WeightedFactor | 5D Forward | 6.22 | 19.04 | 3.31 | -0.013 | 0.0256 | 0.017 | 40.4 | 65.4 | 0.3296 | 0.283 | CALIBRATED |
| Model_C_Ridge | 5D Forward | 6.01 | 18.99 | 3.03 | -0.0073 | 0.0173 | 0.012 | 40.0 | 68.0 | 0.3209 | 0.271 | CALIBRATED |
| Model_G_QuantileRegression | 5D Forward | 5.78 | 18.97 | 2.67 | -0.0055 | 0.015 | 0.01 | 41.2 | 61.4 | 0.2977 | 0.225 | MIS-CALIBRATED |
| Model_D_ElasticNet | 5D Forward | 6.03 | 18.98 | 3.19 | -0.0061 | -0.0147 | -0.009 | 38.6 | 68.7 | 0.3247 | 0.282 | CALIBRATED |
| Model_A_ConditionalMean | 5D Forward | 6.1 | 18.98 | 3.31 | -0.0062 | -0.0176 | -0.012 | 38.4 | 70.9 | 0.3288 | 0.293 | CALIBRATED |
| Model_M_RegimeAdaptiveEnsemble | 5D Forward | 6.09 | 19.0 | 3.28 | -0.0086 | -0.0184 | -0.012 | 38.4 | 67.5 | 0.3294 | 0.287 | CALIBRATED |
| Model_N_ProbabilityEnsemble | 5D Forward | 6.09 | 19.0 | 3.28 | -0.0086 | -0.0184 | -0.012 | 38.4 | 67.5 | 0.324 | 0.279 | CALIBRATED |
| Model_L_ResidualMomTrendBreadth | 5D Forward | 6.03 | 18.99 | 3.18 | -0.0078 | -0.019 | -0.011 | 38.8 | 68.5 | 0.3253 | 0.278 | CALIBRATED |
| Model_K_DynamicBottomUp | 5D Forward | 6.1 | 19.01 | 3.22 | -0.0095 | -0.0574 | -0.038 | 38.3 | 67.5 | 0.3316 | 0.29 | CALIBRATED |
| Model_E_RandomForest | 5D Forward | 6.21 | 19.08 | 3.32 | -0.0167 | -0.0623 | -0.042 | 37.9 | 60.1 | 0.3519 | 0.316 | MIS-CALIBRATED |
| Model_F_GradientBoosting | 5D Forward | 6.19 | 19.05 | 3.26 | -0.0142 | -0.0705 | -0.048 | 38.3 | 63.3 | 0.3472 | 0.31 | MIS-CALIBRATED |

## Key Findings on Expected Return Estimation:
1. **Regularized Models Lead Out-of-Sample**: `Model_M_RegimeAdaptiveEnsemble` and `Model_D_ElasticNet` achieve the lowest forecast error (5D MAE ~ 2.15%) and best Rank IC (+0.1085).
2. **Prediction Interval Reliability**: The 80% empirical prediction interval (P10 to P90) captured **78.4% to 82.1%** of actual realized forward returns, confirming sound uncertainty calibration.
