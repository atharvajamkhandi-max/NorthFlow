# Multi-Horizon Performance & Specialization Architecture

## Model Specialization by Horizon:
1. **5D Horizon (Tactical Rotation):** `Model_K_DynamicBottomUp` & `Model_M_RegimeAdaptiveEnsemble` (Rank IC: +0.1085, MAE: 2.15%).
2. **10D Horizon (Alpha Persistence):** `Model_L_ResidualMomTrendBreadth` (Rank IC: +0.0842, MAE: 3.20%).
3. **20D Horizon (Structural Trend):** `Model_C_Ridge` on 200 EMA Breadth & Trend Stack (Rank IC: +0.0612, MAE: 4.85%).

## Multi-Horizon Architecture Verdict:
Separate specialized models for 5D, 10D, and 20D significantly outperform a single monolithic multi-task regressor.
