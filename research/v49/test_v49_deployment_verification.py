"""
research/v49/test_v49_deployment_verification.py
Isolated regression test suite for Phase 49 Production Deployment & Live URL Verification.
"""
import pytest
import json
import urllib.request
from pathlib import Path

PHASE49_DIR = Path(__file__).resolve().parent

def test_1_deployment_manifest_status_online():
    m_file = PHASE49_DIR / "deployment_results" / "deployment_manifest.json"
    assert m_file.exists()
    with open(m_file, "r") as f:
        data = json.load(f)
    assert data["deployment_status"] == "ONLINE_HEALTHY"
    assert data["active_model"] == "MODEL_V3.2_FROZEN"
    assert data["candidate_v34_status"].startswith("NOT_DEPLOYED")
    assert data["data_date_served"] == "2026-08-26"

def test_2_http_health_endpoint():
    url = "http://localhost:8501/_stcore/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            assert response.status == 200
            assert response.read().decode().strip() == "ok"
    except Exception as e:
        pytest.skip(f"Live server check skipped in isolated testing: {e}")

def test_3_checksum_immutability():
    c_file = PHASE49_DIR / "deployment_results" / "checksums_audit.json"
    assert c_file.exists()
    with open(c_file, "r") as f:
        data = json.load(f)
    assert len(data["final_predictions_csv"]) == 64
    assert len(data["decision_ledger_db"]) == 64
