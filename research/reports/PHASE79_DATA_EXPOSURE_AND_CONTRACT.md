# PHASE 79 — NORTHFLOW PUBLIC DATA CONTRACT & PRIVACY SPECIFICATION

**Generated:** 2026-08-28 00:11:33 IST  
**Audience:** Public Web Application Users & Automated Ingestion Pipeline  
**Contract Version:** `PUBLIC_DATA_CONTRACT_V1`  

---

## 1. Publicly Exposed Data (Allowed)

The public Streamlit web application is authorized to display the following analytical information:

1. **Equities & Universe Directory:**
   - Listed NSE Symbols, Company Names, ISINs, and active status.
   - 4-Tier Sector / Industry / Basic Industry hierarchical classifications.
   - Market Cap (₹ Cr) and SME platform designation.
2. **Technical & Momentum Metrics:**
   - 1D, 5D, 20D Price Returns and Close Prices.
   - 20-Day Relative Strength (`rs_20d`) vs Nifty 50.
   - Volume Expansion Ratio (`volume_ratio`) vs 20-day average.
   - 50-day EMA Trend Breadth (% above 50 EMA).
3. **Macro & Sector Aggregate Analytics:**
   - Aggregate Industry / Sector Strength Scores (0–100 scale).
   - Market Regime Synthesis (`WEAK_BEAR`, `STRONG_BULL`, etc.) and allocation multipliers.
   - 4-Quadrant Rotation Trail coordinates (Leading, Improving, Weakening, Lagging).
4. **Model Quant Recommendations:**
   - Point-in-time Model Quant Scores (0–100) and Model Actions (`STRONG BUY`, `BUY`, `WATCH`, `AVOID`).
   - Bounded strictly by the user's active market-cap and SME filter selection.

---

## 2. Protected Internal Data (Forbidden from Public Exposure)

The public application MUST NOT expose:

1. **Raw Server Filesystem Paths:** Local directory roots or user paths.
2. **Model Training Code & Raw Weights:** Intermediate optimization scratchbooks.
3. **Database Schema Internal DDL:** Direct arbitrary SQL query execution consoles.
4. **Private Research Scratch Scripts:** One-off exploratory scripts located in `scratch/`.
5. **Administrative Ingestion Controls:** Bhavcopy fetch / database write triggers in the web UI.
