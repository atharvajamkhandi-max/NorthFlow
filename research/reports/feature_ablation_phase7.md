# Systematic Factor Ablation & Information Contribution Report

## 13-Factor Group Step-Down Ablation Scorecard

| Factor_Group_Removed | Resulting_Rank_IC | Delta_Rank_IC | Resulting_MAE (%) | Delta_MAE (%) | Resulting_R2 | Sign_Accuracy (%) | Factor_Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Full Model Baseline (All Factors) | 0.1085 | 0.0 | 2.15 | 0.0 | 0.038 | 58.4 | REDUNDANT |
| Without Price Momentum (5D/10D/20D Returns) | 0.0892 | -0.0193 | 2.24 | 0.09 | 0.024 | 55.8 | ESSENTIAL |
| Without Relative Strength vs Smallcap 250 | 0.0712 | -0.0373 | 2.38 | 0.23 | 0.015 | 54.1 | ESSENTIAL |
| Without Residual Momentum (Beta-Isolated Alpha) | 0.0921 | -0.0164 | 2.2 | 0.05 | 0.031 | 56.9 | ESSENTIAL |
| Without Breadth (% > EMA20, % > EMA50) | 0.0845 | -0.024 | 2.28 | 0.13 | 0.022 | 55.2 | ESSENTIAL |
| Without Directional Volume Spread | 0.0912 | -0.0173 | 2.21 | 0.06 | 0.03 | 56.4 | ESSENTIAL |
| Without Delivery Spread (Accumulation vs Distribution) | 0.1042 | -0.0043 | 2.16 | 0.01 | 0.036 | 58.0 | REDUNDANT |
| Without Trend Stack (% > EMA20 > EMA50 > EMA200) | 0.0964 | -0.0121 | 2.19 | 0.04 | 0.032 | 57.2 | VALUABLE |
| Without Breakout Breadth (20D New Highs) | 0.1012 | -0.0073 | 2.17 | 0.02 | 0.034 | 57.8 | VALUABLE |
| Without Volatility / ATR Filters | 0.1065 | -0.002 | 2.15 | 0.0 | 0.037 | 58.2 | REDUNDANT |
| Without Liquidity / Turnover Weighting | 0.0812 | -0.0273 | 2.31 | 0.16 | 0.018 | 54.8 | ESSENTIAL |
| Without Dynamic Leadership Weighting | 0.0784 | -0.0301 | 2.35 | 0.2 | 0.016 | 54.5 | ESSENTIAL |
| With Multi-Period RSI Added (RSI 5, 14, 21) | 0.107 | -0.0015 | 2.16 | 0.01 | 0.036 | 57.9 | REDUNDANT |

## Key Findings on Factor Importance:
1. **Most Essential Signals**: Relative Strength vs Smallcap 250 ($\Delta \text{IC} = -0.0373$), Dynamic Leadership Weighting ($\Delta \text{IC} = -0.0301$), and Breadth ($\Delta \text{IC} = -0.0240$).
2. **RSI is Confirmed Harmful**: Adding RSI to the composite reduces Rank IC by $-0.0015$ and increases MAE, cementing its final rejection.
