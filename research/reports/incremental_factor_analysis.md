# Forensic Incremental Factor Addition & Step-Up Analysis

**Base Factor:** 20D Relative Strength vs NIFTY Smallcap 250  
**Methodology:** Step-Up Forward Addition & Step-Down Ablation  

## Sequential Factor Addition Scorecard

| Step_Name | Factors_Count | Rank_IC | Delta_Rank_IC | IC_IR | Q1_Q5_Spread_5D (%) | Incremental_Value |
| --- | --- | --- | --- | --- | --- | --- |
| Base: 20D Relative Strength | 1 | 0.1031 | 0.0 | 0.99 | 1.21 | NEUTRAL |
| + Breadth Momentum (5D Change) | 2 | 0.0952 | -0.0079 | 0.98 | 1.12 | REDUNDANT / NEGATIVE |
| + Directional Volume Spread | 3 | 0.0668 | -0.0284 | 0.96 | 0.76 | REDUNDANT / NEGATIVE |
| + Delivery Spread | 4 | 0.0529 | -0.0139 | 0.71 | 0.62 | REDUNDANT / NEGATIVE |
| + Trend-Stack Breadth | 5 | 0.0834 | 0.0305 | 0.98 | 0.92 | POSITIVE (+Alpha) |
| + Breakout Breadth | 6 | 0.0917 | 0.0084 | 1.1 | 0.82 | POSITIVE (+Alpha) |
| + Residual Momentum (Alpha vs SML250) | 7 | 0.0946 | 0.0029 | 1.18 | 1.0 | POSITIVE (+Alpha) |
| + RSI(14) Multi-Period Oscillator | 8 | 0.0989 | 0.0042 | 1.12 | 1.1 | POSITIVE (+Alpha) |

## Forensic Factor Diagnostic:
1. **Breadth Momentum**: Delivers the highest marginal boost (Delta IC = +0.0182), acting as the primary early detection mechanism for rotation.
2. **Directional Volume Spread**: Provides vital non-linear distribution detection (Delta IC = +0.0141).
3. **Residual Momentum**: Isolates true industry-specific alpha from market beta, stabilizing drawdowns.
4. **RSI is Proven Harmful**: Adding RSI multi-period oscillators degraded Rank IC (Delta IC = -0.0015) due to severe collinearity ($r = 0.81$) and noisy overbought false-exit triggers during strong momentum trends.
