# Final Model Specification Blueprint

| Model_Name | Horizon | Rank_IC | Non_Overlapping_IC | MAE (%) | R2 | Sign_Accuracy (%) | Brier | ECE | Annual_Net_Sharpe_20bps | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Model_M_RegimeAdaptiveEnsemble | 5D Forward | 0.1085 | 0.0985 | 1.98 | 0.038 | 58.4 | 0.2314 | 0.038 | 0.85 | ROBUST |
| Model_L_ResidualMomTrendBreadth | 10D Forward | 0.0842 | 0.078 | 3.1 | 0.042 | 61.2 | 0.2285 | 0.035 | 0.95 | ROBUST |
| Model_C_Ridge_TrendStack | 20D Forward | 0.0612 | 0.055 | 4.65 | 0.048 | 62.5 | 0.224 | 0.032 | 1.05 | ROBUST |
| Model_D_ElasticNet_Shrunk | 5D Forward | 0.0903 | 0.084 | 1.98 | 0.035 | 56.7 | 0.2356 | 0.039 | 0.78 | PROMISING |
| Model_E_RandomForest_Constrained | 5D Forward | 0.0512 | 0.042 | 2.25 | 0.021 | 55.4 | 0.245 | 0.048 | 0.42 | UNSTABLE |
| Model_A_ConditionalMean_Baseline | 5D Forward | 0.0 | 0.0 | 2.45 | 0.0 | 50.0 | 0.25 | 0.05 | 0.0 | BASELINE |