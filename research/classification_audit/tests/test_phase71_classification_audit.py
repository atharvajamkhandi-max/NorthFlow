"""
research/classification_audit/tests/test_phase71_classification_audit.py
==========================================================================
Phase 71 audit test suite.
Tests that classification data is consistent, specific misclassifications
are detected, SME status is inferrable, and audit artifacts are complete.

Run with:
  python -m pytest research/classification_audit/tests/ -v
"""

import sys
import sqlite3
import hashlib
import pandas as pd
import pytest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
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
def stocks_df(conn):
    return pd.read_sql("SELECT symbol, company_name, series, industry, basic_industry, macro_sector, active FROM stocks", conn)


@pytest.fixture(scope="module")
def active_stocks(stocks_df):
    return stocks_df[stocks_df["active"] == 1]


@pytest.fixture(scope="module")
def audit_df():
    p = REPORTS_DIR / "classification_audit.csv"
    assert p.exists(), f"classification_audit.csv not found at {p}. Run phase71_audit_engine.py first."
    return pd.read_csv(str(p))


@pytest.fixture(scope="module")
def conflict_df():
    p = REPORTS_DIR / "CLASSIFICATION_CONFLICT_QUEUE.csv"
    assert p.exists(), f"CLASSIFICATION_CONFLICT_QUEUE.csv not found. Run phase71_conflict_detector.py first."
    return pd.read_csv(str(p))


# ──────────────────────────────────────────────
# TEST 1: Production Immutability
# ──────────────────────────────────────────────
class TestProductionImmutability:
    @pytest.mark.parametrize("fname,info", PRODUCTION_FILES.items())
    def test_production_file_unchanged(self, fname, info):
        fpath = info["path"]
        if not fpath.exists():
            pytest.skip(f"File not found: {fpath}")
        actual = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
        expected = info["expected_sha256"]
        assert actual == expected, (
            f"PRODUCTION IMMUTABILITY VIOLATION: {fname}\n"
            f"  Expected: {expected}\n"
            f"  Actual:   {actual}"
        )


# ──────────────────────────────────────────────
# TEST 2: MAXESTATES — Not in Tea & Coffee
# ──────────────────────────────────────────────
class TestMaxEstates:
    def test_maxestates_exists_in_universe(self, active_stocks):
        row = active_stocks[active_stocks["symbol"] == "MAXESTATES"]
        assert len(row) > 0, "MAXESTATES not found in active stocks"

    def test_maxestates_audit_flagged_as_corrected(self, audit_df):
        row = audit_df[audit_df["symbol"] == "MAXESTATES"]
        assert len(row) > 0, "MAXESTATES not in audit CSV"
        assert row.iloc[0]["change_required"] in ("CORRECTED", "REVIEW_REQUIRED"), (
            "MAXESTATES should be flagged for correction"
        )

    def test_maxestates_proposed_sector_is_real_estate(self, audit_df):
        row = audit_df[audit_df["symbol"] == "MAXESTATES"]
        proposed = row.iloc[0]["proposed_sector"].upper()
        assert "REAL ESTATE" in proposed, (
            f"MAXESTATES proposed_sector should be REAL ESTATE, got '{proposed}'"
        )

    def test_maxestates_conflict_queue_has_flag(self, conflict_df):
        row = conflict_df[conflict_df["symbol"] == "MAXESTATES"]
        assert len(row) > 0, "MAXESTATES should appear in conflict queue"


# ──────────────────────────────────────────────
# TEST 3: PRESTIGE ESTATES — Not in Tea & Coffee
# ──────────────────────────────────────────────
class TestPrestigeEstates:
    def test_prestige_audit_flagged(self, audit_df):
        row = audit_df[audit_df["symbol"] == "PRESTIGE"]
        assert len(row) > 0
        assert row.iloc[0]["change_required"] in ("CORRECTED", "REVIEW_REQUIRED")

    def test_prestige_proposed_real_estate(self, audit_df):
        row = audit_df[audit_df["symbol"] == "PRESTIGE"]
        assert "REAL ESTATE" in row.iloc[0]["proposed_sector"].upper()


# ──────────────────────────────────────────────
# TEST 4: TEAMLEASE — Not in Tea & Coffee
# ──────────────────────────────────────────────
class TestTeamlease:
    def test_teamlease_audit_flagged(self, audit_df):
        row = audit_df[audit_df["symbol"] == "TEAMLEASE"]
        assert len(row) > 0
        assert row.iloc[0]["change_required"] in ("CORRECTED", "REVIEW_REQUIRED")

    def test_teamlease_not_proposed_tea_coffee(self, audit_df):
        row = audit_df[audit_df["symbol"] == "TEAMLEASE"]
        proposed = row.iloc[0]["proposed_sector"].upper()
        assert "TEA" not in proposed and "COFFEE" not in proposed, (
            f"TEAMLEASE should not be in TEA & COFFEE, got '{proposed}'"
        )


# ──────────────────────────────────────────────
# TEST 5: SME Status from Series Code
# ──────────────────────────────────────────────
class TestSMEStatus:
    def test_audit_has_sme_status_column(self, audit_df):
        assert "sme_status" in audit_df.columns

    def test_all_active_stocks_have_sme_status(self, audit_df):
        missing = audit_df["sme_status"].isna() | (audit_df["sme_status"] == "")
        assert missing.sum() == 0, f"{missing.sum()} stocks have missing sme_status"

    def test_sm_series_are_sme(self, active_stocks, audit_df):
        sm_series = active_stocks[active_stocks["series"] == "SM"]["symbol"].tolist()
        if sm_series:
            sme_rows = audit_df[audit_df["symbol"].isin(sm_series)]
            all_sme = (sme_rows["sme_status"] == "SME").all()
            assert all_sme, "All SM-series stocks should have sme_status=SME"

    def test_eq_series_are_non_sme(self, active_stocks, audit_df):
        eq_series = active_stocks[active_stocks["series"] == "EQ"]["symbol"].tolist()
        if eq_series:
            non_sme_rows = audit_df[audit_df["symbol"].isin(eq_series)]
            all_non_sme = (non_sme_rows["sme_status"] == "NON_SME").all()
            assert all_non_sme, "All EQ-series stocks should have sme_status=NON_SME"

    def test_sme_count_in_audit_matches_db(self, active_stocks, audit_df):
        db_sme = active_stocks[active_stocks["series"].isin(SME_SERIES)]["symbol"].nunique()
        audit_sme = (audit_df["sme_status"] == "SME").sum()
        assert abs(db_sme - audit_sme) <= 5, (
            f"SME count mismatch: DB={db_sme}, Audit={audit_sme}"
        )


# ──────────────────────────────────────────────
# TEST 6: EMS Companies (PGEL, AMBER, KAYNES)
# ──────────────────────────────────────────────
class TestEMSCompanies:
    EMS_SYMBOLS = ["PGEL", "AMBER", "KAYNES"]

    def test_ems_companies_in_audit(self, audit_df, active_stocks):
        for sym in self.EMS_SYMBOLS:
            if sym in active_stocks["symbol"].values:
                row = audit_df[audit_df["symbol"] == sym]
                assert len(row) > 0, f"{sym} not found in audit CSV"

    def test_ems_companies_not_misclassified_as_tea(self, audit_df, active_stocks):
        for sym in self.EMS_SYMBOLS:
            if sym in active_stocks["symbol"].values:
                row = audit_df[audit_df["symbol"] == sym]
                if len(row) > 0:
                    proposed = row.iloc[0]["proposed_sector"].upper()
                    assert "TEA" not in proposed, f"{sym} should not be in TEA & COFFEE"


# ──────────────────────────────────────────────
# TEST 7: Travel Tech (IXIGO, YATRA, RATEGAIN)
# ──────────────────────────────────────────────
class TestTravelTech:
    def test_ixigo_industry_reasonable(self, audit_df, active_stocks):
        if "IXIGO" in active_stocks["symbol"].values:
            row = audit_df[audit_df["symbol"] == "IXIGO"]
            if len(row) > 0:
                ind = row.iloc[0]["proposed_industry"].lower()
                sector = row.iloc[0]["proposed_sector"].upper()
                assert "travel" in ind or "online" in ind or "e-commerce" in sector.lower() or "tech" in sector.lower(), (
                    f"IXIGO industry should relate to online travel, got '{ind}'"
                )

    def test_rategain_industry_reasonable(self, audit_df, active_stocks):
        if "RATEGAIN" in active_stocks["symbol"].values:
            row = audit_df[audit_df["symbol"] == "RATEGAIN"]
            if len(row) > 0:
                ind = row.iloc[0]["proposed_industry"].lower()
                assert "travel" in ind or "saas" in ind or "tech" in ind or "it" in ind, (
                    f"RATEGAIN should be travel tech / SaaS, got '{ind}'"
                )


# ──────────────────────────────────────────────
# TEST 8: Universe Size
# ──────────────────────────────────────────────
class TestUniverseSize:
    def test_active_stocks_count(self, active_stocks):
        assert len(active_stocks) == 3028, (
            f"Expected 3028 active stocks, found {len(active_stocks)}"
        )

    def test_audit_covers_all_active_stocks(self, active_stocks, audit_df):
        db_symbols = set(active_stocks["symbol"].tolist())
        audit_symbols = set(audit_df["symbol"].tolist())
        missing = db_symbols - audit_symbols
        assert len(missing) == 0, (
            f"{len(missing)} active stocks missing from audit: {list(missing)[:10]}"
        )

    def test_no_duplicate_symbols_in_audit(self, audit_df):
        dup_count = audit_df["symbol"].duplicated().sum()
        assert dup_count == 0, f"{dup_count} duplicate symbols in audit CSV"


# ──────────────────────────────────────────────
# TEST 9: Audit Artifact Completeness
# ──────────────────────────────────────────────
class TestAuditArtifacts:
    REQUIRED_COLUMNS = [
        "symbol", "company_name", "series", "sme_status",
        "current_sector", "current_industry",
        "proposed_sector", "proposed_industry",
        "classification_confidence", "change_required",
        "reason", "source_1", "review_status",
    ]

    def test_classification_audit_csv_exists(self):
        assert (REPORTS_DIR / "classification_audit.csv").exists()

    def test_conflict_queue_csv_exists(self):
        assert (REPORTS_DIR / "CLASSIFICATION_CONFLICT_QUEUE.csv").exists()

    def test_forensics_report_exists(self):
        assert (REPORTS_DIR / "PHASE71_COMPLETE_CLASSIFICATION_FORENSICS.md").exists()

    def test_top500_risks_exists(self):
        assert (REPORTS_DIR / "TOP500_CLASSIFICATION_RISKS.csv").exists()

    def test_audit_csv_has_required_columns(self, audit_df):
        for col in self.REQUIRED_COLUMNS:
            assert col in audit_df.columns, f"Missing required column: {col}"

    def test_all_stocks_have_proposed_sector(self, audit_df):
        missing = audit_df["proposed_sector"].isna() | (audit_df["proposed_sector"] == "")
        assert missing.sum() == 0, f"{missing.sum()} stocks missing proposed_sector"

    def test_all_stocks_have_classification_confidence(self, audit_df):
        missing = audit_df["classification_confidence"].isna() | (audit_df["classification_confidence"] == "")
        assert missing.sum() == 0, f"{missing.sum()} stocks missing classification_confidence"

    def test_no_unknown_classifications(self, audit_df):
        unknown_sector = (audit_df["proposed_sector"].str.upper() == "UNKNOWN").sum()
        assert unknown_sector == 0, f"{unknown_sector} stocks have proposed_sector=UNKNOWN"


# ──────────────────────────────────────────────
# TEST 10: Multi-Industry Representation
# ──────────────────────────────────────────────
class TestMultiIndustry:
    def test_exposure_v3_has_multi_industry_records(self, conn):
        multi = pd.read_sql(
            "SELECT symbol, COUNT(*) as cnt FROM stock_industry_exposure_v3 GROUP BY symbol HAVING cnt > 1",
            conn,
        )
        assert len(multi) > 0, "Expected some stocks with multiple industry exposures"

    def test_audit_has_additional_industries_column(self, audit_df):
        assert "additional_industries" in audit_df.columns


# ──────────────────────────────────────────────
# TEST 11: No Unknown/Null Sectors in DB
# ──────────────────────────────────────────────
class TestDatabaseQuality:
    def test_no_null_macro_sector(self, active_stocks):
        null_count = active_stocks["macro_sector"].isna().sum()
        assert null_count == 0, f"{null_count} active stocks have NULL macro_sector"

    def test_no_null_industry(self, active_stocks):
        null_count = active_stocks["industry"].isna().sum()
        assert null_count == 0, f"{null_count} active stocks have NULL industry"

    def test_stocks_and_v3_row_count_match(self, active_stocks, conn):
        v3_count = pd.read_sql(
            "SELECT COUNT(DISTINCT symbol) as n FROM stock_classification_master_v3", conn
        ).iloc[0]["n"]
        # v3 should cover all active stocks (may have ≤ ε difference from inactive)
        active_count = len(active_stocks)
        assert abs(v3_count - active_count) <= 10, (
            f"v3 master has {v3_count} unique symbols vs {active_count} active stocks"
        )

    def test_exposure_v3_covers_all_active(self, active_stocks, conn):
        exp_count = pd.read_sql(
            "SELECT COUNT(DISTINCT symbol) as n FROM stock_industry_exposure_v3", conn
        ).iloc[0]["n"]
        active_count = len(active_stocks)
        # Allow small margin for very recent additions
        assert exp_count >= active_count - 10, (
            f"exposure_v3 covers only {exp_count} unique symbols vs {active_count} active stocks"
        )


# ──────────────────────────────────────────────
# TEST 12: Confirmed Corrections
# ──────────────────────────────────────────────
class TestConfirmedCorrections:
    CONFIRMED_CORRECTIONS = {
        "MAXESTATES": "REAL ESTATE",
        "PRESTIGE": "REAL ESTATE",
        "TEAMLEASE": ("STAFFING", "EMPLOYMENT", "HR"),
        "PROTEAN": ("IT", "TECH", "DIGITAL"),
    }

    def test_confirmed_corrections_in_audit(self, audit_df):
        for sym in self.CONFIRMED_CORRECTIONS:
            row = audit_df[audit_df["symbol"] == sym]
            assert len(row) > 0, f"{sym} missing from audit CSV"
            assert row.iloc[0]["change_required"] in ("CORRECTED", "REVIEW_REQUIRED"), (
                f"{sym} should be flagged for correction"
            )

    def test_confirmed_corrections_not_tea_coffee(self, audit_df):
        for sym in ["MAXESTATES", "PRESTIGE", "TEAMLEASE", "PROTEAN", "TEAMGTY", "TPHQ"]:
            row = audit_df[audit_df["symbol"] == sym]
            if len(row) > 0:
                proposed_sector = row.iloc[0]["proposed_sector"].upper()
                assert "TEA" not in proposed_sector and "COFFEE" not in proposed_sector, (
                    f"{sym} should not have proposed_sector=TEA/COFFEE, got '{proposed_sector}'"
                )


# ──────────────────────────────────────────────
# TEST 13: IPO Classifier
# ──────────────────────────────────────────────
class TestIPOClassifier:
    def test_ipo_classifier_importable(self):
        from research.classification_audit.phase71_ipo_classifier import IPOClassifier, process_new_listings
        assert IPOClassifier is not None

    def test_ipo_classifier_rejects_unknown(self):
        conn = sqlite3.connect(str(DB_PATH))
        from research.classification_audit.phase71_ipo_classifier import IPOClassifier
        clf = IPOClassifier(conn)
        result = clf.classify("XYZABC99", "Random XYZ Corp", "EQ")
        conn.close()
        assert result["activation_ready"] is False, "Unknown company should not be auto-activated"

    def test_ipo_classifier_detects_pharma(self):
        conn = sqlite3.connect(str(DB_PATH))
        from research.classification_audit.phase71_ipo_classifier import IPOClassifier
        clf = IPOClassifier(conn)
        result = clf.classify("TESTPHARMA", "ABC Pharma Labs Limited", "EQ")
        conn.close()
        assert result["proposed_sector"] in ("PHARMACEUTICALS", "HEALTHCARE SERVICES"), (
            f"Expected pharma sector, got '{result['proposed_sector']}'"
        )

    def test_ipo_classifier_identifies_sme(self):
        conn = sqlite3.connect(str(DB_PATH))
        from research.classification_audit.phase71_ipo_classifier import IPOClassifier
        clf = IPOClassifier(conn)
        result = clf.classify("SMTEST01", "Test SME Company Ltd", "SM")
        conn.close()
        assert result["sme_status"] == "SME", f"SM series should be SME, got '{result['sme_status']}'"

    def test_ipo_classifier_identifies_mainboard(self):
        conn = sqlite3.connect(str(DB_PATH))
        from research.classification_audit.phase71_ipo_classifier import IPOClassifier
        clf = IPOClassifier(conn)
        result = clf.classify("EQTEST01", "Test Mainboard Company Ltd", "EQ")
        conn.close()
        assert result["sme_status"] == "NON_SME"
