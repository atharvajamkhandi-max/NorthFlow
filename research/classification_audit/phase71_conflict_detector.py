"""
research/classification_audit/phase71_conflict_detector.py
=============================================================
AUDIT-ONLY — ZERO DATABASE WRITES.
Scans every active stock for classification anomalies and outputs
CLASSIFICATION_CONFLICT_QUEUE.csv to research/reports/.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))

DB_PATH = BASE / "data" / "market_flow.db"
REPORTS_DIR = BASE / "research" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# Keyword contradiction rules
# (trigger_patterns_in_name, allowed_industry_keywords, conflict_label)
# ─────────────────────────────────────────────
NAME_INDUSTRY_RULES = [
    (
        ["estates", "realty", "realtors", "properties", "housing", "developers", "township"],
        ["real estate", "housing", "construction", "realty", "infrastructure", "cement", "building"],
        "LIKELY_REAL_ESTATE_IN_WRONG_SECTOR",
    ),
    (
        ["software", "technologies", "infotech", "digital", "data", "cyber", "cloud", "egov"],
        ["software", "it", "technology", "digital", "fintech", "saas", "e-gov", "tech", "information"],
        "TECH_NAME_WRONG_INDUSTRY",
    ),
    (
        ["pharma", "drugs", "laboratories", "biotech", "life sciences", "healthcare", "hospitals", "medical"],
        ["pharma", "drug", "biotech", "healthcare", "hospital", "medical", "diagnostic", "health", "life science"],
        "PHARMA_HEALTH_NAME_WRONG_INDUSTRY",
    ),
    (
        ["bank", "banking"],
        ["bank", "finance", "lending", "credit", "nbfc"],
        "BANK_NAME_WRONG_INDUSTRY",
    ),
    (
        ["staffing", "human resources", "manpower", "workforce", "recruitment", "teamlease"],
        ["staffing", "hr", "employment", "workforce", "manpower", "placement"],
        "STAFFING_NAME_WRONG_INDUSTRY",
    ),
    (
        ["insurance"],
        ["insurance"],
        "INSURANCE_NAME_WRONG_INDUSTRY",
    ),
    (
        ["media", "entertainment", "production", "broadcast", "film", "television"],
        ["media", "entertainment", "broadcast", "content", "film", "television"],
        "MEDIA_NAME_WRONG_INDUSTRY",
    ),
    (
        ["logistics", "freight", "courier", "shipping", "cargo"],
        ["logistics", "freight", "courier", "shipping", "transport"],
        "LOGISTICS_NAME_WRONG_INDUSTRY",
    ),
]

SME_SERIES = {"SM", "ST", "SZ"}
NON_SME_SERIES = {"EQ", "BE", "BZ"}


def _name_matches(company_name: str, triggers: list) -> bool:
    name_lower = company_name.lower()
    return any(t in name_lower for t in triggers)


def _industry_matches(industry: str, allowed: list) -> bool:
    ind_lower = (industry or "").lower()
    return any(a in ind_lower for a in allowed)


def detect_conflicts(conn):
    print("[CONFLICT DETECTOR] Loading stocks...")
    stocks = pd.read_sql(
        "SELECT symbol, company_name, series, industry, basic_industry, macro_sector, active FROM stocks",
        conn,
    )
    active = stocks[stocks["active"] == 1].copy()
    print(f"  Active stocks: {len(active):,}")

    print("[CONFLICT DETECTOR] Loading exposure_v3...")
    exposure = pd.read_sql(
        "SELECT symbol, industry as exp_industry, sector as exp_sector, confidence as exp_confidence, rationale FROM stock_industry_exposure_v3",
        conn,
    )
    exp_primary = exposure.drop_duplicates("symbol", keep="first")

    print("[CONFLICT DETECTOR] Loading classification_master_v3...")
    try:
        v3_cols = [r[1] for r in conn.execute("PRAGMA table_info(stock_classification_master_v3)").fetchall()]
        name_col = "primary_industry_name" if "primary_industry_name" in v3_cols else "industry_key"
        v3 = pd.read_sql(
            f"SELECT symbol, sector_key, industry_key, {name_col} as v3_industry_name, confidence as v3_confidence FROM stock_classification_master_v3",
            conn,
        )
        v3_primary = v3.drop_duplicates("symbol", keep="first")
    except Exception as e:
        print(f"  Warning: could not load v3 master: {e}")
        v3_primary = pd.DataFrame(columns=["symbol", "sector_key", "industry_key", "v3_industry_name", "v3_confidence"])

    df = active.merge(exp_primary, on="symbol", how="left")
    df = df.merge(
        v3_primary.rename(columns={"sector_key": "v3_sector_key", "industry_key": "v3_industry_key"}),
        on="symbol",
        how="left",
    )

    conflicts = []
    for _, row in df.iterrows():
        sym = row["symbol"]
        name = str(row.get("company_name") or "")
        series = str(row.get("series") or "EQ")
        industry = str(row.get("industry") or "")
        macro_sector = str(row.get("macro_sector") or "")
        exp_industry = str(row.get("exp_industry") or "")
        exp_sector = str(row.get("exp_sector") or "")
        exp_conf = str(row.get("exp_confidence") or "")
        v3_ind = str(row.get("v3_industry_name") or "")

        issues = []

        # 1. Name vs Industry contradiction
        for triggers, allowed, label in NAME_INDUSTRY_RULES:
            if _name_matches(name, triggers) and not _industry_matches(industry, allowed):
                exp_ok = _industry_matches(exp_industry, allowed)
                issues.append((label, f"Name implies '{label.split('_')[0].title()}' but stocks.industry='{industry}' (exp_v3='{exp_industry}', aligned={exp_ok})"))

        # 2. stocks.macro_sector vs exposure_v3.sector mismatch
        if exp_sector and exp_sector.upper() != macro_sector.upper():
            issues.append(("SECTOR_MISMATCH", f"stocks.macro_sector='{macro_sector}' vs exposure_v3.sector='{exp_sector}'"))

        # 3. stocks.industry vs exposure_v3.industry mismatch (zero word overlap)
        if exp_industry and industry:
            ind_words = set(industry.lower().split())
            exp_words = set(exp_industry.lower().split())
            stop_words = {"and", "the", "of", "for", "a", "in", "&"}
            ind_words -= stop_words
            exp_words -= stop_words
            if ind_words and exp_words and len(ind_words & exp_words) == 0:
                issues.append(("INDUSTRY_MISMATCH", f"stocks.industry='{industry}' vs exposure_v3.industry='{exp_industry}'"))

        # 4. Missing exposure_v3 record
        if not exp_industry:
            issues.append(("NO_EXPOSURE_RECORD", "No stock_industry_exposure_v3 record found"))

        # 5. UNKNOWN classification
        if industry.upper() in ("UNKNOWN", "", "N/A") or macro_sector.upper() in ("UNKNOWN", "", "N/A"):
            issues.append(("UNKNOWN_CLASSIFICATION", f"industry='{industry}', macro_sector='{macro_sector}'"))

        inferred_sme = "SME" if series in SME_SERIES else ("NON_SME" if series in NON_SME_SERIES else "UNKNOWN")

        if issues:
            primary_issue = issues[0][0]
            all_issues = " | ".join(f"{i[0]}: {i[1]}" for i in issues)
            conflicts.append({
                "symbol": sym,
                "company_name": name,
                "series": series,
                "inferred_sme_status": inferred_sme,
                "current_macro_sector": macro_sector,
                "current_industry": industry,
                "exposure_v3_sector": exp_sector,
                "exposure_v3_industry": exp_industry,
                "exposure_v3_confidence": exp_conf,
                "v3_master_industry": v3_ind,
                "primary_conflict": primary_issue,
                "all_conflicts": all_issues,
                "conflict_count": len(issues),
                "review_status": "REVIEW_REQUIRED",
            })

    return pd.DataFrame(conflicts)


def compute_structural_qc(conn):
    single_ind = pd.read_sql(
        "SELECT industry, COUNT(*) as cnt FROM stocks WHERE active=1 GROUP BY industry HAVING cnt=1",
        conn,
    )
    giant_ind = pd.read_sql(
        "SELECT industry, COUNT(*) as cnt FROM stocks WHERE active=1 GROUP BY industry ORDER BY cnt DESC LIMIT 10",
        conn,
    )
    sector_counts = pd.read_sql(
        "SELECT macro_sector, COUNT(*) as cnt FROM stocks WHERE active=1 GROUP BY macro_sector ORDER BY cnt DESC",
        conn,
    )
    unknown = pd.read_sql(
        "SELECT COUNT(*) as n FROM stocks WHERE active=1 AND (industry='UNKNOWN' OR macro_sector='UNKNOWN' OR industry IS NULL OR macro_sector IS NULL)",
        conn,
    )
    no_exp = pd.read_sql(
        "SELECT COUNT(*) as n FROM stocks s WHERE s.active=1 AND NOT EXISTS (SELECT 1 FROM stock_industry_exposure_v3 e WHERE e.symbol=s.symbol)",
        conn,
    )
    return {
        "single_company_industries": single_ind,
        "giant_industries": giant_ind,
        "sector_counts": sector_counts,
        "unknown_count": int(unknown["n"].iloc[0]),
        "no_exposure_count": int(no_exp["n"].iloc[0]),
    }


def main():
    print("=" * 60)
    print("PHASE 71 - CLASSIFICATION CONFLICT DETECTOR")
    print("MODE: AUDIT ONLY - ZERO DATABASE WRITES")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    conflict_df = detect_conflicts(conn)
    print(f"\n[RESULT] Total conflicted stocks: {len(conflict_df):,}")

    print("\n[STRUCTURAL QC]")
    qc = compute_structural_qc(conn)
    print(f"  Unknown classifications: {qc['unknown_count']:,}")
    print(f"  No exposure_v3 record: {qc['no_exposure_count']:,}")
    print(f"  Single-company industries: {len(qc['single_company_industries']):,}")
    print(f"\n  TOP 10 LARGEST INDUSTRIES:")
    print(qc["giant_industries"].to_string(index=False))
    print(f"\n  SINGLE-COMPANY INDUSTRIES (orphan risk):")
    print(qc["single_company_industries"].to_string(index=False))

    out_path = REPORTS_DIR / "CLASSIFICATION_CONFLICT_QUEUE.csv"
    conflict_df.to_csv(str(out_path), index=False)
    print(f"\n[SAVED] {out_path}")
    print(f"        Total conflicts: {len(conflict_df):,}")

    if not conflict_df.empty:
        print("\n[CONFLICT TYPE BREAKDOWN]")
        breakdown = conflict_df.groupby("primary_conflict")["symbol"].count().sort_values(ascending=False)
        for k, v in breakdown.items():
            print(f"  {k}: {v:,}")

    conn.close()
    return conflict_df, qc


if __name__ == "__main__":
    main()
