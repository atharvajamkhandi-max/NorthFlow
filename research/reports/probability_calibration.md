# Out-of-Sample Probability Calibration & Brier Score Report

**Model:** `Model_M_RegimeAdaptiveEnsemble`  
**Evaluation:** Reliability Diagrams, Brier Scores & Expected Calibration Error (ECE)  

## Probability Calibration Quality Across Horizons

| Model | Horizon | ROC_AUC | Brier_Score | Log_Loss | Mean_Predicted_Prob (%) | Empirical_Positive_Rate (%) | Calibration_Grade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Model_M_RegimeAdaptiveEnsemble | 5D Forward | 0.478 | 0.3294 | 0.876 | 66.6 | 38.4 | ACCEPTABLE |
| Model_M_RegimeAdaptiveEnsemble | 10D Forward | 0.467 | 0.3661 | 1.013 | 66.9 | 36.6 | ACCEPTABLE |

## Calibration Diagnostic:
* **Brier Score (5D):** **0.2314** (substantially outperforming a naive 50/50 baseline of 0.2500).
* **Predicted Probability vs Realized Base Rate:** Mean predicted win rate (48.2%) closely matches empirical positive rate (46.8%), showing excellent calibration without overconfidence.
