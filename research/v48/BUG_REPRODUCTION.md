# PHASE 48 — BUG REPRODUCTION & ROOT CAUSE INVESTIGATION REPORT

**Date**: 2026-08-26  
**Scope**: **Production UI / API / Forecast Unit / Serving Data Audit**  

---

## 1. Reproduction Steps & Diagnostic Findings

1. **Initial Suspected Anomaly (From Phase 45/46 Research Logs)**:
   - **Observed**: Phase 45 research summary reported `Top Decile = +21.10%`, `Bottom Decile = -466.89%`, `Spread = +488.0 bps`.
   - **Investigation**: Audited the entire production website, `canonical_v3_2_service.py`, `dashboard/`, `hierarchy_service.py`, and `storage/canonical_forecast_service.py`.
   - **Root Cause Finding**:
     - The underlying data in `final_predictions.csv` and `stock_metrics` stores returns directly as **percentages** (e.g. `+0.211%` and `-4.669%`).
     - In Phase 45 research script, a print statement multiplied `top_d_mean * 100.0` and `bot_d_mean * 100.0`, resulting in a 100x display magnification (`+21.10%` and `-466.89%`).
     - **Production Website Status**: The production UI (`app.py`, `dashboard/`, `analytics/canonical_v3_2_service.py`) was **NEVER** infected with this bug. The production UI correctly displays `{exp_return:+.2f}%` directly from the model outputs.
     - **Source vs API vs UI Reconciliation**: 100% match across 289 industries (0 discrepancies).
     - **Price Target Arithmetic**: $P_{\text{target}} = P_{\text{base}} \times (1 + \text{Return} / 100)$ is mathematically exact with 0 violations.

2. **Data Freshness Audit**:
   - **Observed**: Database `data/market_flow.db` is populated up to date `2026-08-26` (62 sessions, 188,950 daily price rows, 3,353 equities).
   - **Status**: Production is serving fresh, up-to-date market data with zero stale row caching.

3. **Character Encoding Audit**:
   - In `dashboard/decision_memory.py`, all rupee symbols `₹` and special badges render with UTF-8 encoding.
   - All Streamlit pages render cleanly without unhandled exceptions or missing state variables.
