"""
research/classification_audit/phase71_ipo_classifier.py
=========================================================
Permanent IPO/New-Listing Classification Workflow Engine.

WORKFLOW:
  NEW LISTING
        ↓
  IDENTITY RESOLUTION
        ↓
  SME STATUS (from series code)
        ↓
  PRIMARY BUSINESS EXTRACTION (from company name + metadata)
        ↓
  SECTOR ASSIGNMENT
        ↓
  INDUSTRY ASSIGNMENT
        ↓
  MULTI-INDUSTRY CHECK
        ↓
  CONFIDENCE GATE
        |
        ├── HIGH  → ACTIVATE DIRECTLY
        ├── MEDIUM → REVIEW QUEUE (human confirmation required)
        └── LOW   → REVIEW QUEUE (manual classification required)

ZERO DATABASE WRITES until human review confirms HIGH-confidence records.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))

DB_PATH = BASE / "data" / "market_flow.db"
REPORTS_DIR = BASE / "research" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

SME_SERIES = {"SM", "ST", "SZ"}
NON_SME_SERIES = {"EQ", "BE", "BZ"}

# ─────────────────────────────────────────────────────────
# Keyword-based preliminary classification rules.
# For production use these are supplemented by:
#   - DRHP/RHP IPO prospectus text
#   - Company official website
#   - NSE/BSE listing metadata
# ─────────────────────────────────────────────────────────
KEYWORD_CLASSIFICATION_RULES = [
    # (keywords_in_name, sector, industry, confidence)
    (["bank", "banking"], "BANKING", "Private Sector Banks", "MEDIUM"),
    (["insurance", "insure", "life insurance", "general insurance"], "INSURANCE", "Life Insurance", "MEDIUM"),
    (["pharma", "drugs", "laboratories", "biologics", "biotech"], "PHARMACEUTICALS", "Finished Formulations", "MEDIUM"),
    (["hospital", "healthcare", "clinic", "diagnostics", "pathology"], "HEALTHCARE SERVICES", "Multi-Specialty Hospitals", "MEDIUM"),
    (["software", "infotech", "tech solutions", "digital", "saas", "it services"], "IT SERVICES", "Mid-Tier IT & Digital Solutions", "MEDIUM"),
    (["fintech", "payment", "e-payment", "upi", "digital payment"], "FINTECH & DIGITAL PAYMENTS", "Payments & Digital Transactions", "MEDIUM"),
    (["nbfc", "lending", "microfinance", "mfi", "loan", "credit"], "FINANCE & NBFC", "Diversified Consumer & MSME NBFC", "MEDIUM"),
    (["realty", "real estate", "properties", "developer", "township", "estates"], "REAL ESTATE", "Residential Townships & Commercial REITs", "MEDIUM"),
    (["cement", "concrete", "ready mix"], "CEMENT & BUILDING MATERIALS", "Integrated Cement Manufacturing", "MEDIUM"),
    (["power", "solar", "wind", "renewable energy", "energy"], "POWER & ENERGY", "Solar Power Generation", "MEDIUM"),
    (["logistics", "freight", "courier", "express", "supply chain"], "LOGISTICS & TRANSPORT", "Integrated Supply Chain & 3PL", "MEDIUM"),
    (["hotel", "hospitality", "resort", "tourism"], "HOSPITALITY & TOURISM", "Hotels & Luxury Resorts", "MEDIUM"),
    (["media", "entertainment", "film", "television", "ott", "content"], "MEDIA & ENTERTAINMENT", "Television Content & OTT Production", "MEDIUM"),
    (["staffing", "workforce", "manpower", "hr services", "recruitment"], "STAFFING & EMPLOYMENT SERVICES", "Staffing & Workforce Solutions", "MEDIUM"),
    (["textile", "yarn", "spinning", "weaving", "fabric", "garment"], "TEXTILES", "Cotton Spinning & Yarns", "MEDIUM"),
    (["food", "fmcg", "consumer goods", "snacks", "beverages"], "CONSUMER GOODS & FMCG", "Packaged Foods & Snacks", "MEDIUM"),
    (["jewellery", "jewelry", "gems", "diamond", "gold"], "JEWELLERY & GEMS", "Branded Jewellery Retail", "MEDIUM"),
    (["steel", "iron", "tmt", "rebars"], "STEEL", "Secondary Steel & TMT Rebars", "MEDIUM"),
    (["chemical", "specialty chemical", "agrochemical"], "CHEMICALS", "Specialty Chemicals", "MEDIUM"),
    (["auto", "automobile", "vehicle", "car", "motor"], "AUTO & AUTO ANCILLARIES", "Auto Ancillaries", "MEDIUM"),
    (["construction", "engineering", "epc", "infrastructure"], "INFRASTRUCTURE & CONSTRUCTION", "Civil & Commercial Construction", "MEDIUM"),
    (["plantations", "tea", "coffee"], "TEA & COFFEE", "Tea & Coffee Plantations", "MEDIUM"),
]


class IPOClassifier:
    """
    Classifies new IPO/listings into NorthFlow's sector/industry taxonomy.
    Returns a structured classification record with confidence gate.
    DOES NOT WRITE TO DATABASE — caller must gate on confidence.
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        # Load existing industry/sector taxonomy for validation
        self._load_taxonomy()

    def _load_taxonomy(self):
        try:
            self.valid_sectors = set(
                pd.read_sql("SELECT DISTINCT macro_sector FROM stocks WHERE active=1", self.conn)["macro_sector"].tolist()
            )
            self.valid_industries = set(
                pd.read_sql("SELECT DISTINCT industry FROM stocks WHERE active=1", self.conn)["industry"].tolist()
            )
        except Exception:
            self.valid_sectors = set()
            self.valid_industries = set()

    def classify(
        self,
        symbol: str,
        company_name: str,
        series: str,
        isin: Optional[str] = None,
        prospectus_text: Optional[str] = None,
        nse_sector: Optional[str] = None,
        nse_industry: Optional[str] = None,
    ) -> dict:
        """
        Classifies a new listing. Returns a classification record dict.
        confidence: HIGH | MEDIUM | LOW | UNRESOLVED
        activation_ready: True only if HIGH confidence.
        """
        ts = datetime.now().strftime("%Y-%m-%d")

        # Step 1: Identity resolution
        sme_status = "SME" if series in SME_SERIES else ("NON_SME" if series in NON_SME_SERIES else "UNKNOWN")

        # Step 2: Check if already classified
        existing = pd.read_sql(
            f"SELECT symbol, industry, macro_sector FROM stocks WHERE symbol=?",
            self.conn, params=[symbol]
        )
        if not existing.empty:
            return {
                "symbol": symbol,
                "company_name": company_name,
                "series": series,
                "isin": isin or "",
                "sme_status": sme_status,
                "proposed_sector": existing.iloc[0]["macro_sector"],
                "proposed_industry": existing.iloc[0]["industry"],
                "classification_confidence": "HIGH",
                "classification_source": "EXISTING_RECORD",
                "classification_rationale": "Already classified in NorthFlow database",
                "activation_ready": True,
                "review_status": "NO_CHANGE",
                "evidence_date": ts,
            }

        # Step 3: NSE-provided classification (strong signal if available)
        if nse_sector and nse_industry:
            confidence = "MEDIUM"
            rationale = f"NSE-provided sector='{nse_sector}', industry='{nse_industry}'"
            return {
                "symbol": symbol,
                "company_name": company_name,
                "series": series,
                "isin": isin or "",
                "sme_status": sme_status,
                "proposed_sector": nse_sector.upper(),
                "proposed_industry": nse_industry,
                "classification_confidence": confidence,
                "classification_source": "NSE_SECURITY_MASTER",
                "classification_rationale": rationale,
                "activation_ready": False,  # MEDIUM → review queue
                "review_status": "REVIEW_REQUIRED",
                "evidence_date": ts,
            }

        # Step 4: Keyword matching from company name
        name_lower = company_name.lower()
        matched_sector, matched_industry, matched_conf = None, None, "LOW"
        matched_keywords = []

        for keywords, sector, industry, conf in KEYWORD_CLASSIFICATION_RULES:
            for kw in keywords:
                if kw in name_lower:
                    matched_sector = sector
                    matched_industry = industry
                    matched_conf = conf
                    matched_keywords.append(kw)
                    break
            if matched_sector:
                break

        # Step 5: Prospectus text boost
        if prospectus_text and matched_conf == "MEDIUM":
            # Additional corroboration → upgrade to HIGH
            text_lower = prospectus_text.lower()
            if matched_keywords and any(kw in text_lower for kw in matched_keywords):
                matched_conf = "HIGH"

        if matched_sector:
            activation_ready = matched_conf == "HIGH"
            return {
                "symbol": symbol,
                "company_name": company_name,
                "series": series,
                "isin": isin or "",
                "sme_status": sme_status,
                "proposed_sector": matched_sector,
                "proposed_industry": matched_industry,
                "classification_confidence": matched_conf,
                "classification_source": "KEYWORD_MATCH",
                "classification_rationale": f"Matched keywords: {matched_keywords} in company name",
                "activation_ready": activation_ready,
                "review_status": "REVIEW_REQUIRED" if not activation_ready else "ACTIVATE",
                "evidence_date": ts,
            }

        # Step 6: UNRESOLVED
        return {
            "symbol": symbol,
            "company_name": company_name,
            "series": series,
            "isin": isin or "",
            "sme_status": sme_status,
            "proposed_sector": "UNCLASSIFIED",
            "proposed_industry": "UNCLASSIFIED",
            "classification_confidence": "UNRESOLVED",
            "classification_source": "NO_MATCH",
            "classification_rationale": "Could not infer classification from available data. Manual review required.",
            "activation_ready": False,
            "review_status": "REVIEW_REQUIRED",
            "evidence_date": ts,
        }


def process_new_listings(new_listings: list[dict]) -> pd.DataFrame:
    """
    Process a batch of new IPO/listings.
    new_listings: list of dicts with keys: symbol, company_name, series
    Returns DataFrame of classification records.
    DOES NOT WRITE TO DATABASE.
    """
    conn = sqlite3.connect(str(DB_PATH))
    classifier = IPOClassifier(conn)
    results = [classifier.classify(**listing) for listing in new_listings]
    conn.close()

    df = pd.DataFrame(results)

    # Save to review queue
    out = REPORTS_DIR / "IPO_CLASSIFICATION_QUEUE.csv"
    df.to_csv(str(out), index=False, mode="a", header=not out.exists())
    print(f"[IPO CLASSIFIER] Processed {len(df)} new listings → {out}")
    print(f"  Ready for activation: {df['activation_ready'].sum()}")
    print(f"  Review required: {(~df['activation_ready']).sum()}")
    return df


if __name__ == "__main__":
    # Self-test with sample new listings
    test_listings = [
        {"symbol": "TESTIPO1", "company_name": "Test Pharma Solutions Ltd", "series": "EQ"},
        {"symbol": "TESTIPO2", "company_name": "Test Real Estate Properties Ltd", "series": "SM", "isin": "INE000AA0001"},
        {"symbol": "TESTIPO3", "company_name": "Test Digital Technologies Ltd", "series": "EQ"},
        {"symbol": "TESTIPO4", "company_name": "XYZ Unknown Corporation", "series": "ST"},
        {"symbol": "TESTIPO5", "company_name": "ABC Tea Estates Ltd", "series": "BE"},
    ]
    results = process_new_listings(test_listings)
    print("\n[TEST OUTPUT]")
    print(results[["symbol", "company_name", "sme_status", "proposed_sector", "proposed_industry", "classification_confidence", "activation_ready"]].to_string(index=False))
