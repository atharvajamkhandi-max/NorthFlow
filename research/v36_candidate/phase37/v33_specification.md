# MODEL_V3.3_CANDIDATE FROZEN SPECIFICATION
### Architectural Contract, Feature Lineage, Calibration Offsets & Shadow Output Schema

**Specification Version**: 3.3.0-CANDIDATE  
**Frozen Timestamp**: 2026-08-25T00:51:00  
**Status**: **FROZEN FOR SHADOW RESEARCH (Zero Production Modification)**  
**Target Engine**: `research/v36_candidate/phase37/`  
**Active Production Baseline**: `MODEL_V3.2_FROZEN` (**100% UNTOUCHED**)  

---

## 1. Modular Architecture & Feature Flags

`MODEL_V3.3_CANDIDATE` is structured with modular, independently switchable components:
* `use_hgb`: Enables non-linear `HistGradientBoostingRegressor` for 20D expected return forecasting.
* `use_conformal`: Applies out-of-sample conformal volatility quantile scaling ($s = 1.30$) to $P_{10}	ext{--}P_{90}$ intervals.
* `use_regime_60d`: Applies point-in-time regime-conditioned bias offsets to neutralize 60D momentum extrapolation error.
* `use_cross_sectional_rank`: Computes daily percentile ranks and decile assignments across basic industries.
* `use_parent_industry_stock_projection`: Preserves canonical stock-level model-implied projection ($	ext{Price} 	imes (1 + R_{	ext{ind}})$).

---

## 2. Feature Lineage & Point-in-Time Contract

| Feature Name | Source | Timestamp Boundary | Transformation Logic |
| :--- | :--- | :--- | :--- |
| `industry_return_1d` | EOD Bhavcopy | $t \le T$ | 1-Day logarithmic return of industry equal-weighted price |
| `breadth_50` | EOD Bhavcopy | $t \le T$ | % of component stocks trading above their 50-day EMA |
| `CONFIDENCE_SCORE` | V3.2 Engine | $t \le T$ | Point-in-time factor alignment conviction score ($[0, 100]$) |
| `RISK_SCORE` | V3.2 Engine | $t \le T$ | Point-in-time volatility & tail dispersion score ($[0, 100]$) |

* **Zero Lookahead Rule**: Features use only data $\le T$. Outcomes strictly use data $> T$.

---

## 3. Frozen Hyperparameters & Calibration Constants

* **HistGradientBoosting Regressor**:
  * `max_iter`: 80
  * `max_depth`: 4
  * `l2_regularization`: 2.0
  * `learning_rate`: 0.1
  * `random_state`: 42
* **Conformal Quantile Multiplier**:
  * $s = 1.30$ applied as $\hat{P}_q = \hat{Y}_{20D} + (P_q - \hat{Y}_{20D}) 	imes 1.30$.
* **Regime-Aware 60D Offsets**:
  * `WEAK_BULL`: $+12.22\%$ offset
  * `WEAK_BEAR`: $-5.67\%$ offset
  * `SIDEWAYS`: $+4.01\%$ offset
  * `HIGH_VOLATILITY`: $0.00\%$ offset

---

## 4. Shadow Output Schema Contract

Every generated V3.3 prediction record contains:
* `prediction_date` (ISO string `YYYY-MM-DD`)
* `entity_id` & `entity_name`
* `entity_type` (`INDUSTRY`, `SECTOR`, `STOCK`)
* `model_version` (`MODEL_V3.3_CANDIDATE`)
* `forecast_horizon` (`1D`, `5D`, `20D`, `60D`)
* `expected_return` (Float percentage)
* `p10`, `p25`, `p50`, `p75`, `p90` (Calibrated quantile boundaries)
* `direction_probability` (Float percentage $[0, 100]$)
* `confidence_score` & `risk_score` (Floats $[0, 100]$)
* `regime_label` (`WEAK_BULL`, `WEAK_BEAR`, `SIDEWAYS`, `HIGH_VOLATILITY`)
* `rank_percentile` & `rank_decile` (Integers $[1, 10]$ and $[0.0, 1.0]$)
* `rating_action` (`STRONG BUY`, `BUY`, `WATCH`, `NEUTRAL`, `REDUCE`, `AVOID`)
* `prediction_timestamp` (ISO UTC timestamp)
