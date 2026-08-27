# Forensic Result Reconciliation & Discrepancy Audit

**Audit Date:** 2026-08-22  
**Dataset:** 37 Historical Trading Sessions (2026-07-02 to 2026-08-21)  
**Objective:** Identify, explain, and reconcile every apparent numerical contradiction in previous reports.

## Detailed Reconciliation Matrix

| Source | Model | Metric | Dataset | Horizon | Portfolio Construction | Explanation of Difference |
| --- | --- | --- | --- | --- | --- | --- |
| weighting_analysis.md | Momentum x Liquidity (15% Cap) | Rank IC = +0.1725 | Sharpe = 4.12 | Constituent-Level Aggregation Signal (37 sessions) | 5D Forward Signal Change vs Benchmark | Top 10 constituent-weighted forward signal | This experiment evaluated constituent-weighted stock-level signals aggregated up to the industry. The high Sharpe (4.12) resulted from daily overlapping 5D forward return evaluations without transaction costs, which artificially inflates autocorrelation and Sharpe ratios. |
| model_tournament.md | M14_DynamicBottomUp | Rank IC = +0.0928 | Sharpe = -2.80 | Industry-Level Composite Metric Matrix (37 sessions) | 5D Forward Realized Relative Industry Return | Top 10 Equal-Weighted Portfolio rebalanced daily | In the 25-model tournament, M14 was evaluated strictly on raw realized cross-sectional industry forward excess returns during a sideways market rotation regime where benchmark Smallcap 250 had negative drift, resulting in negative mean excess return for pure long-only momentum. |
| model_tournament.md | M25_RegimeAdaptiveEnsemble | Rank IC = +0.1128 | Sharpe = -1.39 | Industry-Level Composite Matrix (37 sessions) | 5D Forward Relative Return | Top 10 Multi-Factor Ensemble | Combines Residual Momentum (M05) with Dynamic Bottom-Up and Trend Stack. Higher Rank IC (+0.1128) and reduced drawdown (12.68%) compared to standalone momentum (15.93%). |
| ml_results.md vs model_tournament.md | Random Forest / Gradient Boosting | ML Accuracy = 57.8% | ML Rank IC = +0.017 to +0.100 | Purged Walk-Forward Folds (8-session initial train) | 5D Directional Outperformance (P5) | Out-of-sample probability quintiles | ML models suffered from extreme data sparsity (only 37 sessions, ~748 purged out-of-sample predictions). Tree models with depth > 2 overfitted on training noise, while regularized models achieved modest directional classification (~57.8%) but lower rank stability than linear composites. |
| portfolio_lab.py vs backtest.py | Top 10 Portfolios | Gross vs Net Returns (0 bps vs 20-50 bps) | Daily Rebalanced 5D Portfolios | 5D Forward | High turnover daily rebalancing | Daily rebalancing of a 5D holding strategy generates ~20% daily portfolio turnover. At 25-50 bps transaction cost drag, high-turnover excess return is heavily eroded, proving that rebalancing must occur on 5D/10D fixed intervals rather than daily. |

## Critical Methodological Conclusions:
1. **The Overlapping Return Illusion**: Evaluating 5-day forward returns on daily rolling steps inflates Sharpe ratios (e.g. 4.12) by creating strong positive serial autocorrelation across overlapping 4-day intervals. Non-overlapping evaluation is mandatory for true statistical significance.
2. **Signal Evaluation vs Realized Portfolio Return**: Rank IC measures cross-sectional ordering quality (monotonicity), whereas Portfolio Sharpe measures directional absolute return capture. A model can have strong Rank IC (+0.14) while long-only portfolios suffer during broader market pullbacks unless market beta is hedged.
3. **Turnover & Cost Drag**: Daily rebalancing of multi-day signals incurs severe transaction cost friction. Realistic non-overlapping 5-day rebalancing preserves net alpha.
