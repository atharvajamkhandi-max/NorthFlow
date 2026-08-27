"""
tests/test_phase72_independent_reaudit.py
=========================================
Phase 72 Test Suite: Independent Re-Audit, Evidence Verification,
Classification Correction, Downstream Propagation, and Production Immutability.
"""

import sys
import sqlite3
import hashlib
import pytest
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

DB_PATH = BASE / "data" / "market_flow.db"
REPORTS_DIR = BASE / "research" / "reports"

PRODUCTION_FILES = {
    "model_v3_2_frozen.py": {
        "path": BASE / "config" / "model_v3_2_frozen.py",
        "expected_sha256": "e350e9209960357d75668ff3dc9fb742162525169ae1f19d7fb7b681beadc756",
    },
    "final_predictions.csv": {
        "path": BASE / "research" / "final_v3" / "results" / "final_predictions.csv",
        "expected_sha256": "52019b780e8b9d714e8f926063dce725541b27335dec47b7f6e66346520bca6b",
    },
    "live_predictions.csv": {
        "path": BASE / "research" / "live_forward" / "ledger" / "live_predictions.csv",
        "expected_sha256": "7950580952b7d3e4d082aeb2c8b48ed892fbe9ce2487d0755255cce81977136e",
    },
    "live_hashes.csv": {
        "path": BASE / "research" / "live_forward" / "ledger" / "live_hashes.csv",
        "expected_sha256": "0010c55813170804e62726ce458ac78cee0394b8995b9f3d2bd8066014c0ca43",
    },
    "promotion_status.json": {
        "path": BASE / "research" / "live_forward" / "promotion_gate" / "promotion_status.json",
        "expected_sha256": "e9761f0b27853f1e2d3635dbe11a36a859b2dee899a1aeb6a15a8f39c1575fa3",
    },
    "decision_ledger.db": {
        "path": BASE / "data" / "decision_ledger.db",
        "expected_sha256": "2a3f7046e8cf072a959c044ddd879a61720deb049eb7ff5cc16703acdf8f7696",
    },
}

SME_SERIES = {"SM", "ST", "SZ"}
NON_SME_SERIES = {"EQ", "BE", "BZ"}

@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(str(DB_PATH))
    yield c
    c.close()

@pytest.fixture(scope="module")
def active_stocks(conn):
    return pd.read_sql("SELECT symbol, company_name, isin, series, sme_status, industry, basic_industry, macro_sector FROM stocks WHERE active=1", conn)

@pytest.fixture(scope="module")
def reaudit_results():
    p = REPORTS_DIR / "PHASE72_REAUDIT_RESULTS.csv"
    assert p.exists(), f"Reaudit results not found at {p}"
    return pd.read_csv(str(p))

@pytest.fixture(scope="module")
def classification_changes():
    p = REPORTS_DIR / "PHASE72_CLASSIFICATION_CHANGES.csv"
    assert p.exists(), f"Classification changes not found at {p}"
    return pd.read_csv(str(p))

# ─────────────────────────────────────────────────────────
# 1. PRODUCTION IMMUTABILITY
# ─────────────────────────────────────────────────────────
class TestProductionImmutabilityPhase72:
    @pytest.mark.parametrize("fname,info", PRODUCTION_FILES.items())
    def test_production_file_hash_unchanged(self, fname, info):
        fpath = info["path"]
        if not fpath.exists():
            pytest.skip(f"File not found: {fpath}")
        actual = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
        expected = info["expected_sha256"]
        assert actual == expected, f"Immutability violated for {fname}: expected {expected}, got {actual}"

# ─────────────────────────────────────────────────────────
# 2. COMPLETE COVERAGE & DATA QUALITY
# ─────────────────────────────────────────────────────────
class TestCompleteCoverageAndQuality:
    def test_all_3028_active_stocks_present(self, active_stocks):
        assert len(active_stocks) == 3028, f"Expected 3028 active stocks, got {len(active_stocks)}"

    def test_no_null_sectors_or_industries(self, active_stocks):
        assert active_stocks["macro_sector"].isna().sum() == 0
        assert active_stocks["industry"].isna().sum() == 0
        assert (active_stocks["macro_sector"] == "UNKNOWN").sum() == 0
        assert (active_stocks["industry"] == "UNKNOWN").sum() == 0

    def test_no_duplicate_symbols(self, active_stocks):
        assert active_stocks["symbol"].duplicated().sum() == 0

    def test_sme_status_consistency(self, active_stocks):
        sme_stocks = active_stocks[active_stocks["series"].isin(SME_SERIES)]
        non_sme_stocks = active_stocks[active_stocks["series"].isin(NON_SME_SERIES)]
        
        assert (sme_stocks["sme_status"] == "SME").all(), "All SM/ST/SZ stocks must have sme_status='SME'"
        assert (non_sme_stocks["sme_status"] == "NON_SME").all(), "All EQ/BE/BZ stocks must have sme_status='NON_SME'"
        assert len(sme_stocks) == 457
        assert len(non_sme_stocks) == 2571

# ─────────────────────────────────────────────────────────
# 3. VERIFIED CORRECTIONS IN DATABASE
# ─────────────────────────────────────────────────────────
class TestVerifiedCorrectionsInDatabase:
    def test_maxestates_is_real_estate(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "MAXESTATES"].iloc[0]
        assert row["macro_sector"] == "REAL ESTATE"
        assert "Commercial Office" in row["industry"] or "Real Estate" in row["industry"]

    def test_prestige_is_real_estate(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "PRESTIGE"].iloc[0]
        assert row["macro_sector"] == "REAL ESTATE"
        assert "Residential Townships" in row["industry"] or "Real Estate" in row["industry"]

    def test_teamlease_is_staffing(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "TEAMLEASE"].iloc[0]
        assert "STAFFING" in row["macro_sector"].upper() or "EMPLOYMENT" in row["macro_sector"].upper()
        assert "Staffing" in row["industry"]

    def test_protean_is_it_services(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "PROTEAN"].iloc[0]
        assert row["macro_sector"] == "IT SERVICES"
        assert "E-Governance" in row["industry"] or "Digital" in row["industry"]

    def test_teamgty_is_finance(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "TEAMGTY"].iloc[0]
        assert row["macro_sector"] == "FINANCE & NBFC"
        assert "Credit Guarantee" in row["industry"] or "Risk Management" in row["industry"]

    def test_tphq_is_media(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "TPHQ"].iloc[0]
        assert row["macro_sector"] == "MEDIA & ENTERTAINMENT"
        assert "Content" in row["industry"] or "OTT" in row["industry"] or "Television" in row["industry"]

    def test_narmada_is_agri(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "NARMADA"].iloc[0]
        assert "AGRI" in row["macro_sector"].upper() or "FOOD" in row["macro_sector"].upper()
        assert "Animal Feed" in row["industry"] or "Feed" in row["industry"]

    def test_dccl_is_finance_sme(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "DCCL"].iloc[0]
        assert row["macro_sector"] == "FINANCE & NBFC"
        assert row["sme_status"] == "SME"

    def test_pccl_is_petrochem_sme(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "PCCL"].iloc[0]
        assert "CHEMICALS" in row["macro_sector"].upper()
        assert "Calcined Petroleum Coke" in row["industry"] or "Carbon" in row["industry"]
        assert row["sme_status"] == "SME"

    def test_occlltd_is_chemicals(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "OCCLLTD"].iloc[0]
        assert row["macro_sector"] == "CHEMICALS"
        assert "Specialty Chemicals" in row["industry"]

    def test_bengalasm_is_holding_nbfc(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "BENGALASM"].iloc[0]
        assert row["macro_sector"] == "FINANCE & NBFC"
        assert "Holding" in row["industry"] or "Investment" in row["industry"]

    def test_ndgl_is_holding_nbfc(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "NDGL"].iloc[0]
        assert row["macro_sector"] == "FINANCE & NBFC"
        assert "Holding" in row["industry"] or "Investment" in row["industry"]

    def test_willamagor_is_holding_nbfc(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "WILLAMAGOR"].iloc[0]
        assert row["macro_sector"] == "FINANCE & NBFC"
        assert "Holding" in row["industry"] or "Investment" in row["industry"]

# ─────────────────────────────────────────────────────────
# 4. TEA & COFFEE PURITY & BENCHMARK
# ─────────────────────────────────────────────────────────
class TestTeaCoffeePurity:
    def test_tea_coffee_constituents_count(self, active_stocks):
        tea_members = active_stocks[active_stocks["macro_sector"] == "TEA & COFFEE"]
        assert len(tea_members) == 21, f"Expected 21 genuine Tea & Coffee stocks, got {len(tea_members)}"

    def test_no_contaminated_stock_in_tea_coffee(self, active_stocks):
        tea_symbols = set(active_stocks[active_stocks["macro_sector"] == "TEA & COFFEE"]["symbol"])
        contaminated = {"MAXESTATES", "PRESTIGE", "TEAMLEASE", "PROTEAN", "TEAMGTY", "TPHQ", "NARMADA", "DCCL", "PCCL", "OCCLLTD", "BENGALASM", "NDGL", "WILLAMAGOR"}
        overlap = tea_symbols & contaminated
        assert len(overlap) == 0, f"Found contaminated symbols still in TEA & COFFEE: {overlap}"

# ─────────────────────────────────────────────────────────
# 5. SPECIFIC SECTOR TEST CASES
# ─────────────────────────────────────────────────────────
class TestSpecificSectorCases:
    def test_travel_tech_cases(self, active_stocks):
        if "IXIGO" in active_stocks["symbol"].values:
            row = active_stocks[active_stocks["symbol"] == "IXIGO"].iloc[0]
            assert "TRAVEL" in row["macro_sector"].upper() or "TECH" in row["macro_sector"].upper() or "IT" in row["macro_sector"].upper()
        if "YATRA" in active_stocks["symbol"].values:
            row = active_stocks[active_stocks["symbol"] == "YATRA"].iloc[0]
            assert "TRAVEL" in row["macro_sector"].upper() or "TECH" in row["macro_sector"].upper() or "IT" in row["macro_sector"].upper()
        if "RATEGAIN" in active_stocks["symbol"].values:
            row = active_stocks[active_stocks["symbol"] == "RATEGAIN"].iloc[0]
            assert "TRAVEL" in row["industry"].upper() or "SAAS" in row["industry"].upper() or "TECH" in row["industry"].upper()

    def test_ems_cases(self, active_stocks):
        for sym in ["PGEL", "AMBER", "KAYNES"]:
            if sym in active_stocks["symbol"].values:
                row = active_stocks[active_stocks["symbol"] == sym].iloc[0]
                assert "EMS" in row["macro_sector"].upper() or "EMS" in row["industry"].upper() or "ELECTRONIC" in row["macro_sector"].upper() or "CONSUMER" in row["macro_sector"].upper()

# ─────────────────────────────────────────────────────────
# 6. MULTI-INDUSTRY REPRESENTATION
# ─────────────────────────────────────────────────────────
class TestMultiIndustryRepresentation:
    def test_multi_industry_table_populated(self, conn):
        df_multi = pd.read_sql("SELECT symbol, macro_sector, niche_subsector, segment_tag FROM company_multi_industry_classification", conn)
        assert len(df_multi) > 0
        bbtc = df_multi[df_multi["symbol"] == "BBTC"]
        assert len(bbtc) >= 2, "BBTC must have primary and secondary segments mapped"

# ─────────────────────────────────────────────────────────
# 7. GLOBAL UNIVERSE & DRILLDOWN INTEGRITY
# ─────────────────────────────────────────────────────────
class TestGlobalUniverseAndDrilldown:
    def test_drilldown_renders_all_constituents(self):
        p13_file = BASE / "dashboard" / "phase13_intelligence_terminal.py"
        content = p13_file.read_text(encoding="utf-8")
        assert "df_stk_view.head(5)" not in content
        assert "df_stk_view.head(10)" not in content
        assert "df_stk_view.head(16)" not in content

    def test_data_quality_dashboard_has_phase72_metrics(self):
        dq_file = BASE / "dashboard" / "data_quality.py"
        content = dq_file.read_text(encoding="utf-8")
        assert "Business Classification Governance & Audit Health (Phase 72)" in content
        assert "PHASE72_V2.0_INDEPENDENT_AUDIT" in content
