"""
research/v50/test_v50_candidate_identity.py
Isolated unit tests for Phase 50 V3.4 Candidate Identity & Live Shadow Alignment Audit.
"""
import pytest
import json
from pathlib import Path

PHASE50_DIR = Path(__file__).resolve().parent

def test_1_governance_resolution_verdict_is_verdict_b():
    g_file = PHASE50_DIR / "audit_results" / "governance_resolution.json"
    assert g_file.exists()
    with open(g_file, "r") as f:
        data = json.load(f)
    assert data["is_exact_match"] is False
    assert "B. LIVE SHADOW IS NOT V3.4" in data["governance_action"]
    assert data["live_shadow_true_identity"] == "MODEL_V3.3_LIVE_FORWARD_FROZEN"
    assert data["v34_candidate_true_identity"] == "MODEL_V3.4_RESEARCH_CANDIDATE"

def test_2_comparison_matrix_identifies_architectural_differences():
    c_file = PHASE50_DIR / "audit_results" / "comparison_matrix.json"
    assert c_file.exists()
    with open(c_file, "r") as f:
        items = json.load(f)
    arch_item = next(i for i in items if i["component"] == "Model Architecture")
    feat_item = next(i for i in items if i["component"] == "Feature Count & Schema")
    assert arch_item["exact_match"] is False
    assert feat_item["exact_match"] is False

def test_3_v34_manifest_specification_locked():
    m_file = PHASE50_DIR / "v34_live_forward_manifest.json"
    assert m_file.exists()
    with open(m_file, "r") as f:
        manifest = json.load(f)
    assert manifest["model_version"] == "MODEL_V3.4_RESEARCH_CANDIDATE"
    assert len(manifest["feature_set"]) == 8
    assert len(manifest["sub_models"]) == 3
    assert len(manifest["manifest_hash"]) == 64

def test_4_existing_v33_evidence_preserved_and_unmodified():
    v42_manifest = PHASE50_DIR.parent / "v42" / "v33_shadow_manifest.json"
    assert v42_manifest.exists()
    with open(v42_manifest, "r") as f:
        data = json.load(f)
    assert data["manifest_hash"] == "e23427b873cb9240954af927b21969564bb7da0e2c2b18649950cbe3bf2f87fc"
