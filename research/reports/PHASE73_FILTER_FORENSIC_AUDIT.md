# PHASE 73 — NORTHFLOW GLOBAL FILTER CONSISTENCY FORENSIC AUDIT

**Timestamp:** 2026-08-27 23:08 IST  
**Status:** `NORTHFLOW_FILTER_FORENSICS_COMPLETE`  
**Investigation Mode:** Read-Only Static & Dynamic Forensic Trace (Zero Production Modifications)  

---

## 1. Executive Summary & Forensic Findings

A comprehensive forensic audit of all universe filtering, caching, state propagation, and downstream consumers was conducted across NorthFlow's data, analytics, and UI presentation layers.

### Key Forensic Discoveries:

1. **Empty / Impossible Universe Fallback to ALL STOCKS:**
   - **Locations:** `dashboard/phase13_intelligence_terminal.py` (lines 76, 87, 107) and `dashboard/industry_flow.py` (line 240).
   - **Root Cause:** Expressions like `if u_ctx["is_filtered"] and u_ctx["eligible_symbols"]:` check Python truthiness of `set()`. When an extreme filter (e.g. Market Cap ≥ ₹9,999,999 Cr or impossible turnover) yields an empty set `set()`, `bool(set())` evaluates to `False`. The code falls into the `else:` branch, which executes an unconstrained SQL query returning **ALL 3,028 ACTIVE STOCKS**.
   - **Severity:** `CRITICAL`

2. **Cache Key Disconnection in Hierarchy Intelligence:**
   - **Location:** `dashboard/components/hierarchy_service.py` -> `get_aggregated_hierarchy_intelligence(selected_date, hierarchy_level_key=None, eligible_symbols=None)`.
   - **Root Cause:** `@st.cache_data(ttl=180)` hashes arguments `(selected_date, hierarchy_level_key, eligible_symbols)`. When callers pass `hierarchy_level_key=None` or `eligible_symbols=None`, the resolution of default hierarchy level or universe context occurs *inside* the function body. Streamlit caches the initial evaluation; subsequent changes to session state or universe filters return stale cached data without re-executing the resolution logic.
   - **Severity:** `HIGH`

3. **Direct Unfiltered Pre-calculated Table Reads in Industry Detail:**
   - **Location:** `dashboard/industry_detail.py` (lines 24-102).
   - **Root Cause:** `db.get_latest_industry_metrics(trade_date=selected_date)` reads pre-computed records directly from the `industry_metrics` SQLite table, which is computed across the universal unfiltered universe (3,028 stocks). The industry detail header (constituent counts, breadth %, score, volume metrics) displays unfiltered numbers even when a restrictive universe filter is active.
   - **Severity:** `HIGH`

4. **SME Status Series Alignment (`SZ` series):**
   - **Location:** `dashboard/components/universe_service.py` (line 197).
   - **Root Cause:** SME mask used `df['series'].isin(['SM', 'ST'])`, missing series `'SZ'` (1 equity), whereas the canonical `sme_status` column in `stocks` correctly identifies all 457 SME platform equities.
   - **Severity:** `MEDIUM`

---

## 2. Complete Inventory of Universe-Dependent Functions & Data Paths

| Function / Component | File | Input Universe | Filters Applied | Cache Key | Session State | Output Symbol Set | Potential Leak / Risk | Severity |
|---|---|---|---|---|---|---|---|---|
| `resolve_user_universe` | `dashboard/components/universe_service.py` | All 3,028 active stocks | SME, Min MCAP, Min Turnover | `(selected_date, include_sme, min_mcap_cr, min_turnover_lakhs)` | Reads preset and custom inputs | Filtered symbol set & tuple | Missing `SZ` series if not using `sme_status` column | `MEDIUM` |
| `get_current_universe_context` | `dashboard/components/universe_service.py` | `resolve_user_universe` | Preset mappings | None (reads session state) | `universe_preset`, `custom_*` | Universe dict with symbols, count, label | Safe wrapper, but depends on cache correctness | `LOW` |
| `get_aggregated_hierarchy_intelligence` | `dashboard/components/hierarchy_service.py` | `stocks` + `stock_metrics` | `eligible_symbols` (if passed) | `(selected_date, hierarchy_level_key, eligible_symbols)` | Reads `hierarchy_level` if None | Aggregated cross-sectional DataFrame | Cache hit on `None` args bypasses dynamic filter changes | `HIGH` |
| `get_canonical_hierarchy_quant_scores` | `analytics/canonical_v3_2_service.py` | `stocks` + `stock_metrics` | None (Unfiltered baseline) | `(selected_date, hierarchy_level_key)` | Reads `hierarchy_level` | Canonical 0-100 quant scores | Pure model baseline (by design immutable) | `NONE` |
| `get_canonical_stock_quant_score` | `analytics/canonical_v3_2_service.py` | `stocks` + `stock_metrics` | `symbol` (optional) | `(selected_date, symbol)` | None | All constituent stocks with quant scores | Filtered downstream by callers | `LOW` |
| `load_sector_overview_data` | `dashboard/industries_explorer.py` | `stock_classification_master_v3` | `eligible_symbols` (if passed) | `@st.cache_data` (if decorated) | None | Sector-level summary + raw DataFrame | Safe when tuple is explicitly passed | `LOW` |
| `render_phase13_intelligence_terminal` | `dashboard/phase13_intelligence_terminal.py` | `get_aggregated_hierarchy_intelligence` | Cascading filters + Active Universe | N/A | `selected_trading_date`, `drilldown` | Filtered aggregate + constituent drilldown | Empty universe truthiness check falls back to all stocks | `CRITICAL` |
| `render_industry_flow` | `dashboard/industry_flow.py` | `get_aggregated_hierarchy_intelligence` | N ≥ Min Constituents + Active Universe | N/A | `selected_drilldown_entity` | Ranked industries + drilldown | Empty universe truthiness check falls back to all stocks | `CRITICAL` |
| `render_stock_screener` | `dashboard/stock_screener.py` | `get_canonical_stock_quant_score` | `u_ctx['eligible_symbols']` + UI sliders | N/A | `scr_sec_sel`, `scr_hier_sel`, `scr_min_score` | Filtered stocks matching screener criteria | Safe subset filtering | `LOW` |
| `render_overview` | `dashboard/overview.py` | `get_aggregated_hierarchy_intelligence` | Active Universe | N/A | None | Overview regime cards & distribution | Dependent on hierarchy_service cache key | `MEDIUM` |
| `render_emerging` | `dashboard/emerging.py` | `get_aggregated_hierarchy_intelligence` | Active Universe | N/A | None | Emerging momentum radar cards | Dependent on hierarchy_service cache key | `MEDIUM` |
| `render_rotation_map` | `dashboard/rotation.py` | `get_aggregated_hierarchy_intelligence` | Active Universe | N/A | None | 4-Quadrant Scatter Bubble Chart | Dependent on hierarchy_service cache key | `MEDIUM` |
| `render_industry_detail` | `dashboard/industry_detail.py` | `industry_metrics` + `db.get_stocks_by_industry` | `u_ctx['eligible_symbols']` (constituents only) | N/A | `selected_industry` | Industry metrics + constituent stocks | Header displays unfiltered DB `stock_count` & breadths | `HIGH` |
| `db.get_stocks_by_industry` | `database/db.py` | `stocks` + `stock_metrics` | `industry_name` | None | None | Raw constituents of industry | Must be filtered by caller using active universe | `LOW` |
| `MarketCapService` | `analytics/market_cap_service.py` | `stock_classification_master_v3` | None | None | None | Valuation mapping | Authoritative market cap query service | `NONE` |

---

## 3. Data Flow Diagram: Canonical Active Universe Propagation

```
+--------------------------------------------------------------------+
|                        USER SIDEBAR FILTERS                        |
|  - Universe Preset (All, SME Off, >= 1k, 5k, 20k, 50k, 100k Cr...) |
|  - Custom Filter (SME Toggle, Min Market Cap, Min Turnover)        |
|  - Session Trading Date                                            |
+--------------------------------------------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|               dashboard/components/universe_service.py             |
|                  resolve_user_universe(date, ...)                  |
|  - Resolves eligible symbols point-in-time                         |
|  - Returns authoritative Dict: eligible_symbols, tuple, count, etc.|
+--------------------------------------------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|                     ACTIVE UNIVERSE CONTRACT                       |
|           ACTIVE_UNIVERSE = { s ∈ STOCKS : passes_filters }        |
|           Tuple explicitly passed to all cached analytics          |
+--------------------------------------------------------------------+
                                  |
         +------------------------+------------------------+
         |                                                 |
         v                                                 v
+------------------------------------+  +------------------------------------+
|      CROSS-SECTIONAL ANALYTICS     |  |       CONSTITUENT DRILLDOWN        |
|   hierarchy_service.py             |  |   phase13, industry_flow, detail   |
|   industries_explorer.py           |  |   - Queries constituents in group  |
|   - Aggregates over ACTIVE_UNIV    |  |   - INTERSECTS with ACTIVE_UNIV    |
|   - Recalculates scores & breadth  |  |   - Empty universe -> 0 rows       |
+------------------------------------+  +------------------------------------+
```

---

## 4. Conclusion & Next Phase

Forensic audit Phase A is complete. All potential failure mechanisms and leakage paths have been mapped with zero modifications to production code.
