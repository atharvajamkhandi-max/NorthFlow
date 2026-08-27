# Failure Analysis & False Positive Diagnostics

## Failure Mode Categories

| Failure Category | Primary Cause | Frequency | Mitigation Implemented |
| :--- | :--- | :--- | :--- |
| **False Positives (Bull Traps)** | Single-stock illiquid spike in N=1-2 constituent industries. | Moderate | Constituent Reliability Metric sqrt(N)/sqrt(10) & Low-Sample Flags. |
| **False Negatives (Missed Compounders)** | Low-volatility steady leaders that do not trigger >1.2x volume ratio. | Low | Inclusion of Trend-Stack Breadth (S_trend). |
| **Distribution Masked by High Delivery** | Institutional block dumping occurring on heavy down-days with high delivery. | Moderate | Directional Volume Spread & Up-vs-Down Delivery Spread. |
| **Regime Whip** | Abrupt broad market gap-downs causing correlated sector drops. | Low | Benchmark isolation via Residual Momentum. |
