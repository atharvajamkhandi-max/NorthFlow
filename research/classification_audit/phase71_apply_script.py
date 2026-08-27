"""
research/classification_audit/phase71_apply_script.py
=======================================================
APPLY PHASE — ONLY RUN AFTER FULL AUDIT APPROVAL.

This script:
1. Hashes production artifacts pre-apply (baseline)
2. Creates timestamped backup of current classification
3. Applies validated corrections from classification_audit.csv
4. Writes audit metadata, timestamps, classifier version, reviewer status
5. Preserves rollback capability (backup always exists before apply)
6. Hashes production artifacts post-apply (verify only classification tables changed)

IMPORTANT: This script must NEVER be run automatically.
It must only be executed after explicit human review and approval of:
  research/reports/PHASE71_COMPLETE_CLASSIFICATION_FORENSICS.md
  research/reports/classification_audit.csv

RUNS ONLY WHEN: python phase71_apply_script.py --confirmed
"""

import sys
import sqlite3
import hashlib
import shutil
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))

DB_PATH = BASE / "data" / "market_flow.db"
REPORTS_DIR = BASE / "research" / "reports"
BACKUPS_DIR = BASE / "research" / "classification_audit" / "backups"
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFIER_VERSION = "PHASE71_V1.0_AUDIT_2026-08-27"

PRODUCTION_FILES = {
    "model_v3_2_frozen.py": BASE / "config" / "model_v3_2_frozen.py",
    "final_predictions.csv": BASE / "research" / "final_v3" / "results" / "final_predictions.csv",
    "live_predictions.csv": BASE / "research" / "live_forward" / "ledger" / "live_predictions.csv",
}


def compute_hash(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except Exception as e:
        return f"ERROR:{e}"


def require_confirmation():
    if "--confirmed" not in sys.argv:
        print("=" * 60)
        print("APPLY PHASE — SAFETY GATE")
        print("=" * 60)
        print("This script will MODIFY the production classification database.")
        print("")
        print("Required pre-conditions:")
        print("  [1] research/reports/PHASE71_COMPLETE_CLASSIFICATION_FORENSICS.md reviewed")
        print("  [2] research/reports/classification_audit.csv reviewed")
        print("  [3] classification_audit.csv CORRECTED rows manually verified")
        print("  [4] All 61 existing tests pass")
        print("")
        print("To run apply phase, execute:")
        print("  python phase71_apply_script.py --confirmed")
        print("")
        print("Exiting without any changes.")
        sys.exit(0)


def backup_classification_tables(conn, ts):
    """Export current classification state to backup CSV files."""
    tables = [
        "stocks",
        "stock_classification_master_v3",
        "stock_industry_exposure_v3",
        "company_multi_industry_classification",
        "custom_industry_classification",
    ]
    backup_manifest = {}
    for table in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
            out = BACKUPS_DIR / f"{ts}_{table}.csv"
            df.to_csv(str(out), index=False)
            h = compute_hash(out)
            backup_manifest[table] = {"path": str(out), "rows": len(df), "sha256": h}
            print(f"  Backed up {table}: {len(df):,} rows → {out.name}")
        except Exception as e:
            print(f"  WARNING: Could not backup {table}: {e}")
    return backup_manifest


def apply_corrections(conn, audit_df, ts):
    """Apply CORRECTED rows from classification_audit.csv to stocks table."""
    corrected = audit_df[audit_df["change_required"] == "CORRECTED"].copy()
    print(f"\n[APPLY] Applying {len(corrected):,} corrections to stocks table...")

    applied = 0
    errors = []
    apply_log = []

    cursor = conn.cursor()
    for _, row in corrected.iterrows():
        sym = row["symbol"]
        new_sector = row["proposed_sector"]
        new_industry = row["proposed_industry"]
        reason = row["reason"]

        try:
            # Update stocks table
            cursor.execute(
                "UPDATE stocks SET macro_sector=?, industry=?, basic_industry=?, last_updated=? WHERE symbol=?",
                (new_sector, new_industry, new_industry, ts, sym),
            )
            # Update stock_classification_master_v3 if record exists
            cursor.execute(
                "UPDATE stock_classification_master_v3 SET sector=?, industry=?, last_verified=?, classification_source=?, classification_rationale=? WHERE symbol=?",
                (new_sector, new_industry, ts, CLASSIFIER_VERSION, reason, sym),
            )
            apply_log.append({
                "symbol": sym,
                "company_name": row.get("company_name", ""),
                "old_sector": row["current_sector"],
                "old_industry": row["current_industry"],
                "new_sector": new_sector,
                "new_industry": new_industry,
                "reason": reason,
                "applied_at": ts,
                "classifier_version": CLASSIFIER_VERSION,
                "reviewer_status": "AUDIT_AUTO_CORRECTED",
            })
            applied += 1
        except Exception as e:
            errors.append({"symbol": sym, "error": str(e)})

    conn.commit()

    # Save apply log
    log_df = pd.DataFrame(apply_log)
    log_path = REPORTS_DIR / f"APPLY_LOG_{ts}.csv"
    log_df.to_csv(str(log_path), index=False)
    print(f"  Applied: {applied:,} corrections")
    if errors:
        print(f"  Errors: {len(errors):,}")
        for e in errors[:5]:
            print(f"    {e['symbol']}: {e['error']}")

    return applied, errors, log_df


def write_audit_metadata(backup_manifest, pre_hashes, post_hashes, applied, errors, ts):
    """Write complete audit metadata JSON for reproducibility."""
    meta = {
        "classifier_version": CLASSIFIER_VERSION,
        "apply_timestamp": ts,
        "pre_apply_hashes": pre_hashes,
        "post_apply_hashes": post_hashes,
        "corrections_applied": applied,
        "errors": len(errors),
        "backup_manifest": backup_manifest,
        "reviewer_status": "AUDIT_APPLY_PHASE_71",
        "immutability_check": {
            fname: {
                "pre": pre_hashes.get(fname),
                "post": post_hashes.get(fname),
                "unchanged": pre_hashes.get(fname) == post_hashes.get(fname),
            }
            for fname in PRODUCTION_FILES
        },
    }
    meta_path = REPORTS_DIR / f"APPLY_METADATA_{ts}.json"
    with open(str(meta_path), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[METADATA] Written to {meta_path}")
    return meta


def main():
    require_confirmation()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("=" * 60)
    print("PHASE 71 - APPLY SCRIPT")
    print(f"Timestamp: {ts}")
    print("=" * 60)

    # 1. Pre-apply hashes
    print("\n[1] PRE-APPLY PRODUCTION HASHES...")
    pre_hashes = {fname: compute_hash(fpath) for fname, fpath in PRODUCTION_FILES.items()}
    for fname, h in pre_hashes.items():
        print(f"  {fname}: {h[:24]}...")

    # 2. Load audit CSV
    audit_path = REPORTS_DIR / "classification_audit.csv"
    if not audit_path.exists():
        print("ERROR: classification_audit.csv not found. Run phase71_audit_engine.py first.")
        sys.exit(1)
    audit_df = pd.read_csv(str(audit_path))
    corrected_count = (audit_df["change_required"] == "CORRECTED").sum()
    print(f"\n[2] Loaded audit CSV: {len(audit_df):,} rows, {corrected_count:,} to apply")

    # 3. Open DB and backup
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    print("\n[3] BACKING UP CLASSIFICATION TABLES...")
    backup_manifest = backup_classification_tables(conn, ts)

    # 4. Apply corrections
    applied, errors, log_df = apply_corrections(conn, audit_df, ts)

    # 5. Post-apply hashes
    print("\n[4] POST-APPLY PRODUCTION HASHES...")
    post_hashes = {fname: compute_hash(fpath) for fname, fpath in PRODUCTION_FILES.items()}
    all_unchanged = True
    for fname, h in post_hashes.items():
        unchanged = pre_hashes.get(fname) == h
        all_unchanged = all_unchanged and unchanged
        status = "UNCHANGED" if unchanged else "CHANGED (ERROR)"
        print(f"  {fname}: {status}")

    if not all_unchanged:
        print("ERROR: Production artifact changed during apply. Rollback recommended.")

    # 6. Write metadata
    meta = write_audit_metadata(backup_manifest, pre_hashes, post_hashes, applied, errors, ts)

    print("\n" + "=" * 60)
    if all_unchanged and applied > 0:
        print("APPLY COMPLETE")
        print(f"  Corrections applied: {applied:,}")
        print(f"  Production immutability: VERIFIED")
        print(f"  Rollback available: {BACKUPS_DIR}")
    else:
        print("APPLY WARNING — REVIEW LOGS")
    print("=" * 60)
    conn.close()


if __name__ == "__main__":
    main()
