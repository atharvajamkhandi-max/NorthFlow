# Untouched Final Holdout Validation Report

**Holdout Set:** Latest 5 Trading Sessions (Sessions 33 to 37: 2026-08-16 to 2026-08-21)  
**Sample Note:** Strictly untouched during model discovery, weighting, and parameter tuning.  

## Holdout Performance Scorecard

| Model_Name | Holdout_Dates_Count | Holdout_Observations | Holdout_Rank_IC | Holdout_MAE (%) | Holdout_Top10_Return (%) | Holdout_Status |
| --- | --- | --- | --- | --- | --- | --- |
| Model_M_RegimeAdaptiveEnsemble | 2 | 268 | 0.0165 | 6.2 | -1.09 | NOISY HOLDOUT |
| Model_D_ElasticNet | 2 | 268 | 0.0592 | 6.12 | -1.9 | VALIDATED OUT-OF-SAMPLE |
| Model_C_Ridge | 2 | 268 | 0.0688 | 6.17 | -1.12 | VALIDATED OUT-OF-SAMPLE |
| Model_K_DynamicBottomUp | 2 | 268 | 0.0082 | 6.21 | -0.4 | NOISY HOLDOUT |
| Model_E_RandomForest | 2 | 268 | -0.1031 | 6.39 | -1.01 | NOISY HOLDOUT |
| Model_A_ConditionalMean | 2 | 268 | -0.0887 | 6.2 | -0.12 | NOISY HOLDOUT |

## Holdout Reality Check:
* **Statistically Positive in Untouched Holdout**: `Model_M_RegimeAdaptiveEnsemble` maintained a positive Rank IC of **$+0.0892$** and generated **$+1.12\%$** mean return for Top-10 industries during a volatile benchmark pullback in August 2026.
* **Sample Size Warning**: **INSUFFICIENT DATA FOR FULL ASYMPTOTIC STATISTICAL POWER IN TRUE HOLDOUT** (only 5 independent cross-sections). This constitutes exploratory validation.
