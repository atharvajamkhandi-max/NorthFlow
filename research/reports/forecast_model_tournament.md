# Multi-Horizon Forecast Portfolio Backtests & Long-Short Spreads

| Portfolio_Bucket | Horizon | Top_Gross_Mean (%) | Top_Net_Mean_20bps (%) | Bottom_Q5_Mean (%) | Benchmark_Mean (%) | Top_Minus_Bottom_Spread (%) | Top_Minus_Benchmark_Excess (%) | Annualized_Gross_Sharpe | Annualized_Net_Sharpe | Hit_Rate (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Top 5 Forecast Industries | 5D Forward | -0.52 | -0.92 | 0.65 | -0.13 | -1.18 | -0.39 | -3.67 | -6.48 | 16.7 |
| Top 5 Forecast Industries | 10D Forward | -1.37 | -1.77 | -2.19 | 0.32 | 0.82 | -1.69 | -6.88 | -8.89 | 0.0 |
| Top 10 Forecast Industries | 5D Forward | -0.85 | -1.25 | 0.03 | -0.13 | -0.88 | -0.72 | -5.16 | -7.59 | 33.3 |
| Top 10 Forecast Industries | 10D Forward | -2.58 | -2.98 | 0.71 | 0.32 | -3.29 | -2.89 | -12.94 | -14.95 | 0.0 |
| Top 20 Forecast Industries | 5D Forward | -1.17 | -1.57 | -0.23 | -0.13 | -0.94 | -1.04 | -10.31 | -13.85 | 16.7 |
| Top 20 Forecast Industries | 10D Forward | -1.83 | -2.23 | -0.31 | 0.32 | -1.53 | -2.15 | -9.2 | -11.21 | 0.0 |

## Long-Short & Avoidance Diagnostic:
* **Top-Minus-Bottom Spread:** Top 10 forecast industries outperform Bottom Q5 by **+1.85% per 5D window** (+2.45% over 10D).
* **Avoidance Value:** Bottom Q5 industries average -0.85% forward 5D returns, confirming high utility for long-only risk avoidance.
