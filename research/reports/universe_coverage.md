# Universe Coverage Audit

**Audit Date:** 2026-08-22  
**Benchmark:** NIFTY SMALLCAP 250  

## Universe Layer Breakdown

| Universe Layer | Count | Historical Sessions | Included in Research | Exclusion Reason |
| --- | --- | --- | --- | --- |
| Active NSE Equities | 3363 | 37 (2026-07-02 to 2026-08-21) | YES | None (100% Included) |
| Official Basic Industries | 135 | 37 (2026-07-02 to 2026-08-21) | YES | Primary Industry Layer |
| Official Macro Sectors | 23 | 37 (2026-07-02 to 2026-08-21) | YES | Macro Aggregation Layer |
| Custom Trading Industries | 5 | 37 (2026-07-02 to 2026-08-21) | YES | Mapped across 21 stocks |
| Custom Trading Segments | 17 | 37 (2026-07-02 to 2026-08-21) | YES | Segment Level Analysis |
| Benchmark (NIFTY SMALLCAP 250) | 1 | 37 (2026-07-02 to 2026-08-21) | YES | Official Benchmark |

## Exclusions & Integrity Rules
* **100% Listed Equities Tracked**: All 3,363 active equities in SQLite are classified with zero UNKNOWN mappings.
* **Granular Basic Industries**: 135 active Official NSE Basic Industries.
* **No Manufactured Data**: Missing history on newer IPOs flagged with `InsufficientHistory` without artificial data creation.
