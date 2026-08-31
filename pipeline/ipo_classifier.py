"""
pipeline/ipo_classifier.py

IPO Auto-Classification Engine
================================
Triggered by daily pipeline whenever a new symbol appears in daily_prices
but has no classification in stock_classification_master_v3.

Strategy:
1. Check stocks table for NSE basic_industry / macro_sector
2. Apply name-keyword heuristics
3. Insert with classification_confidence = 'AUTO_IPO_PENDING'
4. Flag for manual review

Integration:
    from pipeline.ipo_classifier import classify_new_ipos
    classify_new_ipos(conn)  # call at end of daily pipeline
"""

import sqlite3
import logging
from datetime import date

logger = logging.getLogger(__name__)

NSE_BASIC_INDUSTRY_MAP = {
    "Pharmaceuticals":                    ("PHARMACEUTICALS",              "Finished Formulations"),
    "Pharmaceuticals & Biotechnology":    ("PHARMACEUTICALS",              "Biotechnology & Biologicals"),
    "Chemicals":                          ("CHEMICALS",                    "Specialty Chemicals"),
    "Specialty Chemicals":                ("CHEMICALS",                    "Specialty Chemicals"),
    "Agrochemicals":                      ("AGRICULTURE & AGROCHEMICALS",  "Agrochemicals & Pesticides"),
    "Pesticides & Agrochemicals":         ("AGRICULTURE & AGROCHEMICALS",  "Agrochemicals & Pesticides"),
    "Fertilizers & Agrochemicals":        ("FERTILIZERS",                  "Fertilizers & Soil Nutrients"),
    "Fertilisers":                        ("FERTILIZERS",                  "Fertilizers & Soil Nutrients"),
    "IT-Software":                        ("IT SERVICES",                  "Enterprise Software & SaaS"),
    "IT - Software":                      ("IT SERVICES",                  "Enterprise Software & SaaS"),
    "Software & IT Services":             ("IT SERVICES",                  "Enterprise Software & SaaS"),
    "Computer Software - Medium & Small": ("IT SERVICES",                  "Enterprise Software & SaaS"),
    "IT-Hardware":                        ("IT SERVICES",                  "IT Hardware & Peripherals"),
    "Telecom - Equipment & Accessories":  ("TELECOM",                      "Telecom Equipment & Infrastructure"),
    "Telecom - Services":                 ("TELECOM",                      "Mobile Services & Data"),
    "Engineering":                        ("CAPITAL GOODS & MACHINERY",    "Heavy Engineering & Process Plant"),
    "Capital Goods":                      ("CAPITAL GOODS & MACHINERY",    "Heavy Engineering & Process Plant"),
    "Industrial Manufacturing":           ("CAPITAL GOODS & MACHINERY",    "Heavy Engineering & Process Plant"),
    "Industrial Products":                ("CAPITAL GOODS & MACHINERY",    "Heavy Engineering & Process Plant"),
    "Electrical Equipment":               ("ELECTRICAL EQUIPMENT",         "Power & Distribution Transformers"),
    "Power":                              ("POWER",                        "Conventional Thermal & Fossil Power"),
    "Oil & Gas":                          ("OIL & GAS",                    "Refining & Petrochemicals"),
    "Petroleum Products":                 ("OIL & GAS",                    "Refining & Petrochemicals"),
    "Mining":                             ("MINING & MINERALS",            "Coal & Thermal Mining"),
    "Steel":                              ("STEEL",                        "Integrated Steel Plants"),
    "Metals":                             ("METALS & FABRICATION",         "Non-Ferrous Metals & Copper"),
    "Non Ferrous Metals":                 ("METALS & FABRICATION",         "Non-Ferrous Metals & Copper"),
    "Aluminium":                          ("ALUMINIUM & COPPER",           "Primary Aluminium Smelting"),
    "Cement":                             ("CEMENT",                       "Integrated Grey Cement"),
    "Construction":                       ("CONSTRUCTION & INFRASTRUCTURE","Civil & Commercial Construction"),
    "Infrastructure":                     ("CONSTRUCTION & INFRASTRUCTURE","Roads & Highways EPC"),
    "Realty":                             ("REAL ESTATE",                  "Residential Real Estate"),
    "Real Estate":                        ("REAL ESTATE",                  "Residential Real Estate"),
    "Finance":                            ("FINANCE & NBFC",               "Diversified Consumer & MSME NBFC"),
    "NBFC":                               ("FINANCE & NBFC",               "Diversified Consumer & MSME NBFC"),
    "Banks":                              ("BANKING",                      "Private Sector Banks"),
    "Private Sector Bank":                ("BANKING",                      "Private Sector Banks"),
    "Public Sector Bank":                 ("BANKING",                      "Public Sector Banks (PSU)"),
    "Small Finance Bank":                 ("BANKING",                      "Small Finance Banks"),
    "Insurance":                          ("INSURANCE",                    "Life & General Insurance"),
    "Retail":                             ("RETAIL",                       "Specialty Retail"),
    "Consumer Goods":                     ("FMCG & PERSONAL CARE",         "Home & Personal Care Products"),
    "FMCG":                               ("FMCG & PERSONAL CARE",         "Home & Personal Care Products"),
    "Textiles & Apparels":                ("TEXTILES",                     "Garments & Apparel Exports"),
    "Textiles":                           ("TEXTILES",                     "Cotton Spinning & Yarns"),
    "Paper":                              ("PAPER & PACKAGING",            "Paperboard & Packaging Cartons"),
    "Auto Ancillaries":                   ("AUTO ANCILLARIES",             "Precision Auto Engine Components"),
    "Automobiles":                        ("AUTOMOBILE",                   "Passenger Vehicles & SUVs"),
    "Two & Three Wheelers":               ("AUTOMOBILE",                   "Two-Wheelers & Motorcycles"),
    "Commercial Vehicles":                ("AUTOMOBILE",                   "Commercial Vehicles & Trucks"),
    "Transport":                          ("LOGISTICS & SUPPLY CHAIN",     "3PL Logistics & Fleet Haulage"),
    "Logistics":                          ("LOGISTICS & SUPPLY CHAIN",     "3PL Logistics & Fleet Haulage"),
    "Hotels":                             ("HOTELS & HOSPITALITY",         "Luxury Hotels & Resorts"),
    "Hotels & Restaurants":               ("HOTELS & HOSPITALITY",         "Luxury Hotels & Resorts"),
    "Media":                              ("MEDIA & ENTERTAINMENT",        "Broadcasting & OTT Streaming"),
    "Entertainment":                      ("MEDIA & ENTERTAINMENT",        "Film Production & Distribution"),
    "Healthcare":                         ("HEALTHCARE SERVICES",          "Multi-Specialty Hospitals"),
    "Healthcare Services":                ("HEALTHCARE SERVICES",          "Multi-Specialty Hospitals"),
    "Food Processing":                    ("FOOD PROCESSING",              "Packaged Foods & Snacks"),
    "Sugar":                              ("SUGAR & BIO-ETHANOL",          "Sugar Refining & Bio-Ethanol"),
    "Tea & Coffee":                       ("TEA & COFFEE",                 "Tea Plantations & Processing"),
    "Agriculture":                        ("AGRICULTURE & AGROCHEMICALS",  "Agri Trading & Commodity Processing"),
    "Defence":                            ("DEFENCE & AEROSPACE",          "Defence Electronics & Avionics"),
    "Renewable Energy":                   ("RENEWABLE ENERGY",             "Solar PV & Green Hydrogen"),
    "Footwear":                           ("FOOTWEAR",                     "Leather Footwear & Sports Shoes"),
    "Gems & Jewellery":                   ("JEWELLERY",                    "Gold Jewellery & Retail"),
    "Education":                          ("EDUCATION & EDTECH",           "Coaching & Test Prep"),
    "Beverages":                          ("BEVERAGES & DISTILLERIES",     "Indian Made Foreign Liquor (IMFL)"),
    "Electronics":                        ("EMS & ELECTRONICS",            "Consumer Electronics Manufacturing"),
    "Consumer Durables":                  ("CONSUMER DURABLES",            "Consumer Electronics & White Goods"),
    "Water":                              ("WATER TREATMENT",              "Water & Wastewater Treatment Plants"),
    "Staffing":                           ("STAFFING & EMPLOYMENT SERVICES","Workforce Staffing & HR Services"),
    "Exchange Traded Funds (ETF)":        ("EXCHANGE TRADED FUNDS",        "Equity Index ETF"),
    "Mutual Fund Asset Managers (AMC)":   ("CAPITAL MARKETS",              "Mutual Fund Asset Managers (AMC)"),
    "Wealth Broking & Advisory":          ("CAPITAL MARKETS",              "Stockbroking & Wealth Management"),
    "Stockbroking":                       ("CAPITAL MARKETS",              "Stockbroking & Wealth Management"),
}

NAME_KEYWORD_RULES = [
    (["pharma","drugs","biotech","biosciences","therapeutics","life sciences","remedies"],
     "PHARMACEUTICALS","Finished Formulations","MEDIUM"),
    (["hotel","resort","hospitality"],
     "HOTELS & HOSPITALITY","Luxury Hotels & Resorts","HIGH"),
    (["realty","developers","estates limited","properties limited","builders","townships"],
     "REAL ESTATE","Residential Real Estate","HIGH"),
    (["bank","banking"],
     "BANKING","Private Sector Banks","HIGH"),
    (["insurance","assurance","reinsurance"],
     "INSURANCE","Life & General Insurance","HIGH"),
    (["sugar","distillery","distilleries","ethanol"],
     "SUGAR & BIO-ETHANOL","Sugar Refining & Bio-Ethanol","HIGH"),
    (["steel","tmt","rolling","sponge iron"],
     "STEEL","Secondary Steel & TMT Rebars","HIGH"),
    (["cement","lime ","ready mix"],
     "CEMENT","Regional Cement & RMC","HIGH"),
    (["chemical","specialty chem"],
     "CHEMICALS","Specialty Chemicals","MEDIUM"),
    (["logistics","freight","courier","cargo"],
     "LOGISTICS & SUPPLY CHAIN","3PL Logistics & Fleet Haulage","MEDIUM"),
    (["solar","renewable","wind energy","green energy"],
     "RENEWABLE ENERGY","Solar PV & Green Hydrogen","MEDIUM"),
    (["software","technology","infotech","it solutions","digital solutions"],
     "IT SERVICES","Enterprise Software & SaaS","LOW"),
    (["textile","cotton","yarn","apparel","garment","fabric"],
     "TEXTILES","Cotton Spinning & Yarns","MEDIUM"),
    (["foods","food products","nutrition","dairy","spice"],
     "FOOD PROCESSING","Packaged Foods & Snacks","MEDIUM"),
    (["mining","minerals","coal","quarry"],
     "MINING & MINERALS","Coal & Thermal Mining","MEDIUM"),
    (["paper","packaging","carton","board"],
     "PAPER & PACKAGING","Paperboard & Packaging Cartons","MEDIUM"),
    (["rubber","tyre","tire"],
     "TYRES & RUBBER","Tyres & Rubber Products","HIGH"),
    (["jewel","jewellery","gold retail","diamond","gemstone"],
     "JEWELLERY","Gold Jewellery & Retail","HIGH"),
    (["defence","defense","ordnance"],
     "DEFENCE & AEROSPACE","Defence Electronics & Avionics","HIGH"),
    (["hospital","healthcare","clinic","medicare","diagnostics"],
     "HEALTHCARE SERVICES","Multi-Specialty Hospitals","MEDIUM"),
    (["education","edtech","learning","university","coaching"],
     "EDUCATION & EDTECH","Coaching & Test Prep","MEDIUM"),
    (["paint","coating","varnish"],
     "PAINTS & COATINGS","Decorative & Industrial Paints","HIGH"),
    (["capital services","capital advisors","broking","wealth management"],
     "CAPITAL MARKETS","Stockbroking & Wealth Management","MEDIUM"),
    (["capital","finance","finvest","financial services","nbfc","lending","credit"],
     "FINANCE & NBFC","Diversified Consumer & MSME NBFC","LOW"),
    (["power","energy","electricity"],
     "POWER","Conventional Thermal & Fossil Power","LOW"),
    (["aluminium","aluminum","copper","zinc"],
     "ALUMINIUM & COPPER","Primary Aluminium Smelting","MEDIUM"),
]


def _classify_by_name(name: str):
    n = name.lower()
    for keywords, sector, industry, confidence in NAME_KEYWORD_RULES:
        if any(kw in n for kw in keywords):
            return sector, industry, confidence
    return "UNCLASSIFIED", "NEEDS_MANUAL_REVIEW", "NONE"


def classify_new_ipos(conn: sqlite3.Connection) -> dict:
    """
    Find all symbols in daily_prices with no classification in v3,
    attempt auto-classification, and insert with confidence flag.
    """
    today = date.today().isoformat()

    v3_syms = {r[0] for r in conn.execute("SELECT symbol FROM stock_classification_master_v3").fetchall()}
    price_syms = {r[0] for r in conn.execute("SELECT DISTINCT symbol FROM daily_prices").fetchall()}
    new_syms = price_syms - v3_syms

    if not new_syms:
        logger.info("ipo_classifier: No new unclassified symbols found.")
        return {"classified": 0, "unclassified": 0, "skipped": 0}

    logger.info(f"ipo_classifier: Found {len(new_syms)} unclassified symbols.")

    classified = 0
    unclassified = 0
    skipped = 0
    cursor = conn.cursor()

    for sym in sorted(new_syms):
        row = conn.execute("""
            SELECT company_name, series, basic_industry, macro_sector, sme_status
            FROM stocks WHERE symbol = ?
        """, (sym,)).fetchone()

        if not row:
            skipped += 1
            continue

        company_name, series, basic_ind, macro_sec, sme_status = row
        company_name = company_name or sym

        if basic_ind and "ETF" in str(basic_ind).upper():
            sector, industry, confidence = "EXCHANGE TRADED FUNDS", "Equity Index ETF", "HIGH"
        elif basic_ind and basic_ind in NSE_BASIC_INDUSTRY_MAP:
            sector, industry = NSE_BASIC_INDUSTRY_MAP[basic_ind]
            confidence = "NSE_BASIC_INDUSTRY"
        elif macro_sec and macro_sec in NSE_BASIC_INDUSTRY_MAP:
            sector, industry = NSE_BASIC_INDUSTRY_MAP[macro_sec]
            confidence = "NSE_MACRO_SECTOR"
        else:
            sector, industry, confidence = _classify_by_name(company_name)

        rationale = (
            f"IPO Auto-Classification: NSE basic_industry='{basic_ind}', "
            f"macro_sector='{macro_sec}', confidence={confidence}. Requires verification."
        )
        source = "AUTO_IPO_PENDING" if sector != "UNCLASSIFIED" else "UNCLASSIFIED"

        cursor.execute("""
            INSERT OR IGNORE INTO stock_classification_master_v3
            (symbol, company_name, sector, industry, classification_confidence,
             classification_source, classification_rationale, effective_from, last_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (sym, company_name, sector, industry, confidence, source, rationale, today, today))

        if cursor.rowcount > 0:
            if sector == "UNCLASSIFIED":
                unclassified += 1
            else:
                classified += 1

    conn.commit()
    logger.info(f"ipo_classifier done: classified={classified}, unclassified={unclassified}, skipped={skipped}")
    return {"classified": classified, "unclassified": unclassified, "skipped": skipped}


if __name__ == "__main__":
    from pathlib import Path
    DB = Path(__file__).parent.parent / "data" / "market_flow.db"
    import sqlite3 as _sql
    c = _sql.connect(str(DB))
    r = classify_new_ipos(c)
    print(f"IPO Classifier result: {r}")
    c.close()
