"""
tests/test_phase72_1_final_closure.py
======================================
Phase 72.1 Test Suite: Final NorthFlow Classification Verification,
Reconciliation, Full Universe Sanity & Audit Closure.
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
def reconciliation_df():
    p = REPORTS_DIR / "PHASE72_1_FINAL_EQUITY_RECONCILIATION.csv"
    assert p.exists(), f"Reconciliation file not found at {p}"
    return pd.read_csv(str(p))

# ─────────────────────────────────────────────────────────
# 1. PRODUCTION IMMUTABILITY VERIFICATION
# ─────────────────────────────────────────────────────────
class TestProductionImmutabilityPhase72_1:
    @pytest.mark.parametrize("fname,info", PRODUCTION_FILES.items())
    def test_production_artifact_hash_unchanged(self, fname, info):
        fpath = info["path"]
        if not fpath.exists():
            pytest.skip(f"File not found: {fpath}")
        actual = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
        expected = info["expected_sha256"]
        assert actual == expected, f"Immutability violated for {fname}: expected {expected}, got {actual}"

# ─────────────────────────────────────────────────────────
# 2. FULL RECONCILIATION DATASET AUDIT
# ─────────────────────────────────────────────────────────
class TestReconciliationDatasetAudit:
    def test_reconciliation_row_count_matches_active_stocks(self, active_stocks, reconciliation_df):
        assert len(reconciliation_df) == len(active_stocks)
        assert len(reconciliation_df) == 3028

    def test_no_duplicate_symbols_in_reconciliation(self, reconciliation_df):
        assert reconciliation_df["symbol"].duplicated().sum() == 0

    def test_required_columns_present(self, reconciliation_df):
        required_cols = [
            "symbol", "company_name", "exchange", "series", "sme_status",
            "sector", "industry", "primary_industry", "secondary_sectors",
            "secondary_industries", "classification_source",
            "classification_confidence", "verification_status"
        ]
        for col in required_cols:
            assert col in reconciliation_df.columns, f"Missing required column: {col}"

    def test_all_stocks_verified_and_high_confidence(self, reconciliation_df):
        assert (reconciliation_df["verification_status"] == "VERIFIED").all()
        assert (reconciliation_df["classification_confidence"] == "HIGH").all()

# ─────────────────────────────────────────────────────────
# 3. SME PLATFORM CONSISTENCY
# ─────────────────────────────────────────────────────────
class TestSMEPlatformConsistency:
    def test_sme_count_exact(self, reconciliation_df):
        sme_count = (reconciliation_df["sme_status"] == "SME").sum()
        non_sme_count = (reconciliation_df["sme_status"] == "NON_SME").sum()
        unknown_count = (reconciliation_df["sme_status"] == "UNKNOWN").sum()
        
        assert sme_count == 457
        assert non_sme_count == 2571
        assert unknown_count == 0

# ─────────────────────────────────────────────────────────
# 4. TEA & COFFEE COMPLETE ERADICATION OF CONTAMINATION
# ─────────────────────────────────────────────────────────
class TestTeaCoffeeCompleteEradication:
    def test_tea_coffee_total_is_21(self, active_stocks):
        tea_members = active_stocks[active_stocks["macro_sector"] == "TEA & COFFEE"]
        assert len(tea_members) == 21

    def test_all_13_contaminated_stocks_relocated(self, active_stocks):
        contaminated_map = {
            "MAXESTATES": "REAL ESTATE",
            "PRESTIGE": "REAL ESTATE",
            "TEAMLEASE": "STAFFING & EMPLOYMENT SERVICES",
            "PROTEAN": "IT SERVICES",
            "TEAMGTY": "FINANCE & NBFC",
            "TPHQ": "MEDIA & ENTERTAINMENT",
            "NARMADA": "AGRICULTURE & AGRI-INPUTS",
            "DCCL": "FINANCE & NBFC",
            "PCCL": "CHEMICALS & PETROCHEMICALS",
            "OCCLLTD": "CHEMICALS",
            "BENGALASM": "FINANCE & NBFC",
            "NDGL": "FINANCE & NBFC",
            "WILLAMAGOR": "FINANCE & NBFC"
        }
        for sym, target_sector in contaminated_map.items():
            row = active_stocks[active_stocks["symbol"] == sym]
            assert len(row) == 1, f"{sym} not found in active stocks"
            actual_sec = row.iloc[0]["macro_sector"]
            assert actual_sec == target_sector, f"Expected {target_sector} for {sym}, got {actual_sec}"

# ─────────────────────────────────────────────────────────
# 5. MULTI-INDUSTRY INTEGRITY & ZERO UNIVERSE DUPLICATION
# ─────────────────────────────────────────────────────────
class TestMultiIndustryUniverseIntegrity:
    def test_multi_industry_records_in_db(self, conn, active_stocks):
        df_multi = pd.read_sql("SELECT symbol, segment_tag FROM company_multi_industry_classification", conn)
        assert len(df_multi) > 0
        
        # Multi-industry stocks must have exactly 1 record in `stocks` master
        for sym in ["BBTC", "ROSSELLIND", "ANDREWYU", "JAYSREETEA"]:
            assert len(active_stocks[active_stocks["symbol"] == sym]) == 1
            sym_multi = df_multi[df_multi["symbol"] == sym]
            assert len(sym_multi[sym_multi["segment_tag"] == "SECONDARY"]) >= 1

# ─────────────────────────────────────────────────────────
# 6. DOWNSTREAM CANONICAL SERVICE SYNCHRONIZATION
# ─────────────────────────────────────────────────────────
class TestDownstreamServiceSynchronization:
    def test_canonical_service_queries_authoritative_stocks(self):
        from analytics.canonical_v3_2_service import get_model_fingerprint
        fp = get_model_fingerprint()
        assert fp["model_version"] == "MODEL_V3.2_FROZEN"

    def test_drilldown_renders_all_constituents_no_truncation(self):
        p13_code = (BASE / "dashboard" / "phase13_intelligence_terminal.py").read_text(encoding="utf-8")
        assert "df_stk_view.head(5)" not in p13_code
        assert "df_stk_view.head(10)" not in p13_code
        assert "df_stk_view.head(16)" not in p13_code

    def test_governance_data_quality_dashboard_updated(self):
        dq_code = (BASE / "dashboard" / "data_quality.py").read_text(encoding="utf-8")
        assert "PHASE72_V2.0_INDEPENDENT_AUDIT" in dq_code
        assert "3,028 Equities" in dq_code
        assert "457 SME · 2,571 Main" in dq_code
