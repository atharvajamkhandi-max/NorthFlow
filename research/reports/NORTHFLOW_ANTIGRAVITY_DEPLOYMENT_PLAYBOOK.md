# NORTHFLOW ANTIGRAVITY PRODUCTION DEPLOYMENT PLAYBOOK

**Version:** 1.0  
**Target:** Continuous Controlled Releases via Antigravity Pair Programming  

---

## 1. The 15-Step Non-Negotiable Development Loop

For every future enhancement, UI refinement, or maintenance task:

1. **User Request Intake:** Review explicit requirements and identify affected modules.
2. **Forensic Audit First:** Inspect live runtime state, schema, and current behavior before modifying any code.
3. **Reproduction Test:** If fixing a defect, write a standalone test in `scratch/` reproducing the exact failure.
4. **Minimal Isolated Fix:** Modify only the targeted lines of code. Preserve all unrelated modules and comments.
5. **Targeted Unit & Integration Tests:** Run specific pytest suites for the touched component.
6. **Full Regression Suite:** Execute `python -m pytest tests/ research/v73_filter_consistency/ research/classification_audit/tests/ -q` (372/372 passing required).
7. **Secret & Security Scan:** Verify no credentials or internal paths were introduced.
8. **Protected SHA-256 Hash Verification:** Run `p74_verify_all_production_hashes.py` to confirm all 6 core files match baseline byte-for-byte.
9. **Performance Latency Verification:** Confirm page compute latency remains < 150 ms.
10. **Browser / UI Smoke Test:** Test user journey across all presets (ALL, 500 Cr, 1000 Cr, 50k Cr, Empty Universe).
11. **Git Commit:** Create an atomic, descriptive commit.
12. **Push to Remote:** Push to private GitHub repository (`main` branch).
13. **CI Release Gate Execution:** GitHub Actions CI executes automated security, hash, and pytest checks.
14. **Automatic Production Deployment:** Streamlit Community Cloud auto-deploys the validated commit to public live URL.
15. **Release Record Sign-Off:** Generate release report and audit trail in `research/reports/`.
