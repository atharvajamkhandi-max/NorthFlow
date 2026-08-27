# MODEL TOURNAMENT & ML DIAGNOSTIC REPORT
**Champion**: `Existing_Deterministic_V1` (Rank IC = `+0.1143`)  

---

### Machine Learning Failure Mode Diagnosis
1. **Objective Function Mismatch**:
   * Standard GBDT (XGBoost, LightGBM) and linear regressors minimize symmetric point-wise MSE ($L_2$ loss). In financial return distributions with heavy tails, MSE overfits extreme outliers rather than preserving cross-sectional rank monotonicity.
2. **Signal-to-Noise Ratio Deficit**:
   * Tree models partition volatile return noise into spurious leaves, resulting in negative out-of-sample Rank ICs (`-0.21` to `-0.25`).
3. **Regime Non-Stationarity**:
   * Multi-collinear features destabilize unconstrained regression weights during market regime transitions.
