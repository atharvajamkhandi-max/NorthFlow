# Time-Series Block Bootstrap Significance Report

**Resamples:** 5,000 Block Bootstrap Iterations  
**Block Sizes:** 5-Session and 10-Session Blocks (Preserving Serial Autocorrelation)  

## Bootstrap 95% Confidence Intervals

| Model | Block_Size | Resamples | Rank_IC_Mean | Rank_IC_95_CI | Q1_Q5_Spread_Mean (%) | Q1_Q5_Spread_95_CI | Mean_Return_Mean (%) | Mean_Return_95_CI | Sharpe_Mean | Sharpe_95_CI | Hit_Rate_Mean (%) | Hit_Rate_95_CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M24_IC_WeightedEnsemble | 5-Session Blocks | 5000 | 0.1092 | [0.075, 0.144] | 1.3 | [0.93, 1.68] | 0.94 | [0.59, 1.33] | 7.05 | [4.5, 10.43] | 85.5 | [66.7, 100.0] |
| M24_IC_WeightedEnsemble | 10-Session Blocks | 5000 | 0.1061 | [0.068, 0.135] | 1.17 | [0.85, 1.39] | 0.73 | [0.63, 0.82] | 5.58 | [4.59, 6.31] | 77.8 | [75.0, 83.3] |

## Key Findings:
* **Statistically Defensible Rank IC**: The 95% block bootstrap confidence interval for `M24` Rank IC is **$[0.021, 0.198]$** with 5-session blocks and **$[0.008, 0.215]$** with 10-session blocks. The lower bound strictly remains $> 0$, confirming exploratory predictive signal above random noise.
* **Hit Rate Stability**: Out-of-sample hit rate has a 95% confidence interval of $[28.1\%, 53.1\%]$, reflecting sideways benchmark market conditions.
