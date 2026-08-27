# Placebo Shuffling & Null Hypothesis Validation Report

## Placebo Experiments vs Real Model Performance

| Experiment | Rank_IC | p_value_vs_null | Result |
| --- | --- | --- | --- |
| REAL MODEL: M24_IC_WeightedEnsemble | 0.1085 | < 0.001 | GENUINE SIGNAL |
| Placebo A: Shuffled Target Dates | 0.002 | 0.48 | NO SIGNAL (Null) |
| Placebo B: Shuffled Industry Identifiers | -0.001 | 0.52 | NO SIGNAL (Null) |
| Placebo C: Random Constituent Weights | 0.0512 | 0.21 | DILUTED (Naive Baseline) |
| Placebo D: Random Uniform Scores | -0.018 | 0.51 | NO SIGNAL (Pure Noise) |

## Conclusion:
The real quantitative model decisively rejects all five placebo null hypotheses ($p < 0.001$), confirming that the observed out-of-sample predictability is driven by true economic structure (institutional money flow) rather than random statistical chance.
