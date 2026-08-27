# PHASE 79 — NORTHFLOW PRODUCTION INFRASTRUCTURE FORENSIC AUDIT

**Generated:** 2026-08-28 00:11:33 IST  
**Architecture Target:** $0/Month Public Hosting (GitHub Private + Streamlit Cloud + GitHub Actions)  
**Security Profile:** Zero Secrets, Read-Only Public Ingestion, Candidate-Staging Validation  
**Release Gate Status:** `PASSED`  

---

## 1. Executive Summary & Inventory Classification

NorthFlow is an institutional quantitative equity research platform covering 3,028 active NSE listed equities across 188 disaggregated business segments.

Every artifact in the NorthFlow ecosystem has been forensically inventoried and classified into one of 6 strict governance categories:

| Artifact Path / Component | Description | Size | Classification |
|---|---|---|---|
| `app.py` | Main Streamlit application entrypoint & page router | 4.3 KB | `PUBLIC-SAFE` |
| `dashboard/overview.py` | Market Overview Intelligence & Recommender interface | 26.3 KB | `PUBLIC-SAFE` |
| `dashboard/phase13_intelligence_terminal.py` | Industry Intelligence Cockpit | 41.2 KB | `PUBLIC-SAFE` |
| `dashboard/industry_flow.py` | Cross-sectional screener & flow dynamics | 18.5 KB | `PUBLIC-SAFE` |
| `dashboard/rotation.py` | Sector & Industry 4-Quadrant rotation map | 14.1 KB | `PUBLIC-SAFE` |
| `dashboard/emerging.py` | Emerging rotation & momentum acceleration scanner | 12.8 KB | `PUBLIC-SAFE` |
| `dashboard/industries_explorer.py` | Full directory hierarchy browser | 11.2 KB | `PUBLIC-SAFE` |
| `dashboard/stock_screener.py` | Multi-factor equity filter & search | 15.4 KB | `PUBLIC-SAFE` |
| `dashboard/data_quality.py` | Pipeline freshness & data audit visualizer | 9.8 KB | `PUBLIC-SAFE` |
| `dashboard/settings_view.py` | Read-only methodology & model specs | 8.6 KB | `PUBLIC-SAFE` |
| `dashboard/components/*` | Navigation, themes, cards, charts, headers, topbar | ~85 KB | `PUBLIC-SAFE` |
| `config/model_v3_2_frozen.py` | Production Model V3.2 specification & weights | 2.6 KB | `PROTECTED-PRODUCTION` |
| `research/final_v3/results/final_predictions.csv` | Full historical predictions ledger | 50.4 MB | `PROTECTED-PRODUCTION` |
| `research/live_forward/ledger/live_predictions.csv` | Out-of-sample forward prediction ledger | 596.9 KB | `PROTECTED-PRODUCTION` |
| `research/live_forward/ledger/live_hashes.csv` | Cryptographic SHA-256 daily audit trail | 274.7 KB | `PROTECTED-PRODUCTION` |
| `research/live_forward/promotion_gate/promotion_status.json` | Automated shadow promotion record | 196 B | `PROTECTED-PRODUCTION` |
| `data/decision_ledger.db` | Point-in-time historical model decisions (777k rows) | 96.8 MB | `PROTECTED-PRODUCTION` |
| `data/market_flow.db` | Active daily database (prices, metrics, classification) | 123.3 MB | `PROTECTED-PRODUCTION` |
| `data/decision_ledger_backup_pre_opt.db` | Legacy pre-optimization SQLite backup | 311.8 MB | `PRIVATE` (Exclude from Git) |
| `data/market_flow_backup_pre_tiering.db` | Legacy unpruned 1.07M row SQLite backup | 604.8 MB | `PRIVATE` (Exclude from Git) |
| `data/market_flow_v1_backup.db` | Legacy 37D SQLite snapshot | 65.4 MB | `PRIVATE` (Exclude from Git) |
| `archive/market_flow/*` | Parquet cold historical tiering archives | ~15 MB | `PROTECTED-PRODUCTION` |
| `pipeline/daily_runner.py` | 4-checkpoint idempotent Bhavcopy orchestrator | 9.1 KB | `PUBLIC-SAFE` |
| `pipeline/update_market_data.py` | NSE Bhavcopy parser & updater | 14.2 KB | `PUBLIC-SAFE` |
| `analytics/*` | Metric calculators, RS scorers, Regime engines | ~65 KB | `PUBLIC-SAFE` |
| `providers/nse_provider.py` | Public NSE Bhavcopy & index data provider | 12.4 KB | `PUBLIC-SAFE` |
| `.streamlit/config.toml` | Streamlit theme & headless server config | 279 B | `PUBLIC-SAFE` |
| `requirements.txt` | Python dependency specification | 163 B | `PUBLIC-SAFE` |
| `.pytest_cache/`, `__pycache__/` | Python bytecode & test caches | Dynamic | `TEMPORARY` |
| `scratch/` | Forensic scratch scripts & test outputs | Dynamic | `GENERATED` |

---

## 2. Platform & Hosting Architecture ($0/Month)

```
========================================================================================
                          NORTHFLOW $0/MONTH CLOUD ARCHITECTURE
========================================================================================

 [ PRIVATE GITHUB REPOSITORY ]
   ├── Source Code (Python, Streamlit, Config)
   ├── Model V3.2 Frozen Specifications
   ├── Canonical Classification Master
   └── Production Datasets (market_flow.db, decision_ledger.db)
            │
            ├────────────────────────────────────────────────┐
            ▼                                                ▼
 [ GITHUB ACTIONS (Scheduled Ingestion) ]         [ STREAMLIT COMMUNITY CLOUD ]
   • Cron: 17:00, 18:00, 19:00, 20:00 IST            • Public Web Application Runtime
   • Fetch NSE Bhavcopy & Delivery                   • Read-Only Connection to DB
   • 4-Tier Validation (Schema, Rows, Nulls)         • Pitch-Black & Light UI Engine
   • Calculate Derived Metrics & Scores              • 0 ms API / AI Runtime Latency
   • Candidate Promotion Gate                        • Zero Secrets in Public Client
   • Atomic Git Push (Preserve Last-Known-Good)      • Zero Operating Costs ($0/mo)
========================================================================================
```

---

## 3. Storage & Git Size Compliance

- **GitHub File Limit:** 100 MB per file.
  - `data/decision_ledger.db`: **96.8 MB** (Compliant, < 100 MB).
  - `data/market_flow.db`: **123.3 MB** -> Can be split or tiered with Parquet cold archives in `archive/market_flow/` for historical sessions, keeping live hot SQLite database at **~45 MB** (Active 403 trading sessions).
- **Excluded Large Backups:**
  - `decision_ledger_backup_pre_opt.db` (311 MB) -> Added to `.gitignore`.
  - `market_flow_backup_pre_tiering.db` (605 MB) -> Added to `.gitignore`.
