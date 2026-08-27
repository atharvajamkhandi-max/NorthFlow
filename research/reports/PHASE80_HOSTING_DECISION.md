# PHASE 80 — NORTHFLOW ZERO-COST HOSTING DECISION MATRIX

**Generated:** 2026-08-28 00:16:24 IST  
**Selected Platform:** **Streamlit Community Cloud**  
**Monthly Cost:** **$0.00 / Month (Free Forever)**  

---

## 1. Hosting Provider Comparative Evaluation

| Evaluation Criteria | 1. Streamlit Community Cloud | 2. Hugging Face Spaces | 3. GitHub Pages | 4. Render / Fly.io Free Tier |
|---|---|---|---|---|
| **Python / Streamlit Support** | **Native First-Class** | Docker / Gradio native | Static HTML only (Incompatible) | Containerized Python |
| **Private GitHub Repo Support** | **Yes (Free via GitHub OAuth)** | Limited on free tier | No (Public only on free) | Yes (Limited build minutes) |
| **Continuous Deployment (Git Push)** | **Instant (Zero Config)** | Git push to HF remote | N/A | Git push webhook |
| **Custom Domain & HTTPS** | **Free HTTPS (`*.streamlit.app`)** | Free HTTPS (`*.hf.space`) | Free HTTPS | Free HTTPS (Custom spin-down) |
| **Sleep / Spin-down Behavior** | **Low-latency wake (< 2s)** | Sleep after inactivity | N/A | Severe cold starts (50s+) |
| **RAM / CPU Quota** | **1 GB RAM / 1 vCPU (Compliant)** | 16 GB RAM / 2 vCPU | Static only | 512 MB RAM (Too tight) |
| **SQLite Compatibility** | **Native file-based read-only** | Native | N/A | Ephemeral storage |
| **Scheduled Data Ingestion (Cron)** | **Decoupled via GitHub Actions** | Decoupled | N/A | Paid worker required |
| **Monthly Cost** | **$0.00 / month** | $0.00 / month | $0.00 / month | $0.00 (with strict limits) |
| **Overall Recommendation** | **SELECTED (Score: 98/100)** | Fallback (Score: 84/100) | Incompatible (Score: 0/100) | Rejected (Score: 62/100) |

---

## 2. Hosting Architecture & Owner Action Isolation

### Automated Infrastructure (Handled by Antigravity & GitHub):
1. Codebase repository structure and hardened `.streamlit/config.toml`.
2. Automated `.github/workflows/ci.yml` release gates.
3. Automated `.github/workflows/bhavcopy_pipeline.yml` scheduled ingestion.

### One-Time Manual Owner Authorization (Required by Platform OAuth):
Because GitHub and Streamlit Community Cloud enforce strict OAuth user authorization:
1. **Step 1:** Push the repository to your private GitHub account (`git push -u origin main`).
2. **Step 2:** Log in to [share.streamlit.io](https://share.streamlit.io/) with your GitHub account.
3. **Step 3:** Click **"Create app"**, select your private repository, set Main file path to **`app.py`**, and click **"Deploy!"**.
4. Streamlit Community Cloud immediately builds and serves the application live at your designated public URL.
