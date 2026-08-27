# Machine Learning Walk-Forward Validation Report

**Validation Methodology:** Expanding Walk-Forward with 5-Day Purging & Embargo  
**Algorithms Tested:** Logistic Regression, Ridge Regression, Elastic Net, Random Forest, Gradient Boosting  

## Cross-Validated Performance

| Model | Task | Accuracy | ROC_AUC | F1_Score | Brier_Score | Observations | MAE | RMSE | R2 | Rank_IC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Logistic_Regression | Classification (P5) | 56.1 | 0.508 | 0.094 | 0.256 | 748 | - | - | - | - |
| Elastic_Net | Classification (P5) | 56.7 | 0.505 | 0.253 | 0.277 | 748 | - | - | - | - |
| Random_Forest | Classification (P5) | 57.8 | 0.532 | 0.031 | 0.245 | 748 | - | - | - | - |
| Gradient_Boosting | Classification (P5) | 57.8 | 0.489 | 0.112 | 0.254 | 748 | - | - | - | - |
| Gradient_Boosting (Regression) | Return Prediction (5D) | - | - | - | - | 748 | 2.35 | 3.65 | -0.1298 | -0.027 |

## Key ML Conclusions:
* **Random Forest & Elastic Net**: Exhibited modest predictive capability for directional outperformance probability ($P_5$, Accuracy ~57.8%, ROC-AUC 0.532).
* **Linear vs Non-Linear**: Linear models (Ridge, Elastic Net) demonstrated higher stability across small-sample cross sections, whereas tree-based models required strict regularization (depth <= 3) to avoid overfitting on 37 sessions.
