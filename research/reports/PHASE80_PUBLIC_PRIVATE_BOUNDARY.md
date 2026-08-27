# PHASE 80 — NORTHFLOW PUBLIC / PRIVATE DATA BOUNDARY SPECIFICATION

**Generated:** 2026-08-28 00:16:24 IST  
**Specification:** `PUBLIC_PRIVATE_DATA_BOUNDARY_V1`  

---

## 1. Boundary Matrix

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             PUBLIC DATA PERIMETER                                │
├──────────────────────────────────────────────────────────────────────────────────┤
│ • 3,028 Listed Equities (Symbol, Company Name, Industry, Market Cap)             │
│ • Market Regime Classification & Aggregation Scores                              │
│ • 188 Disaggregated Industry Research Cards & Metric Breakdowns                  │
│ • Model Quant Scores & Bounded Action Signals (STRONG BUY, BUY, WATCH, AVOID)    │
│ • Relative Strength (20D RS), Volume Ratio, and 50-EMA Breadth KPIs              │
│ • 4-Quadrant Rotation Trail Coordinates                                          │
└──────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼  [STRICTLY ISOLATED]
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            PRIVATE ASSETS & METADATA                             │
├──────────────────────────────────────────────────────────────────────────────────┤
│ • Private Source Code Repository & Internal Git Commit History                   │
│ • GitHub Actions Secrets & PAT Tokens                                            │
│ • Raw Unindexed Ingestion Scratch Files & Staging Tables                         │
│ • Internal Forensic Audit Logs & Research Notebooks in `scratch/`                │
│ • Future Administrator Portals & Role Management Credentials                     │
└──────────────────────────────────────────────────────────────────────────────────┘
```
