# ⚡ Enterprise B2B Multi-Touch Attribution & Budget Optimization Engine

[![Enterprise CI Pipeline](https://github.com/Ali-datasmith/Marketing-ROI-Tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/Ali-datasmith/Marketing-ROI-Tracker/actions/workflows/ci.yml)
[![CodeQL Analysis](https://github.com/Ali-datasmith/Marketing-ROI-Tracker/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/Ali-datasmith/Marketing-ROI-Tracker/actions/workflows/codeql-analysis.yml)
[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked](https://img.shields.io/badge/mypy-strict-brightgreen.svg)](https://mypy-lang.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

```
====================================================================================================
                        MARKETING ROI & MULTI-TOUCH ATTRIBUTION COMMAND CENTER
====================================================================================================
[ Ingestion: Polars ] ---> [ Modeling: DuckDB SQL ] ---> [ AI Synthesis: Gemini 3.5 ] ---> [ Executive UI ]
====================================================================================================
```

> **Enterprise Edition v2.0**: High-performance B2B multi-touch attribution engine built with zero-copy Polars ingestion, DuckDB vectorized SQL window functions, Gemini 3.5 Flash structured AI executive insights, Argon2 security gate, interactive budget optimization simulator, and FPDF2 dark executive PDF generation.

---

## ☁️ Streamlit Community Cloud Deployment

This repository is optimized for 1-click deployment on **Streamlit Community Cloud**:

1. Fork or push this repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository and configure:
   - **Main file path**: `app.py`
   - **Python version**: `3.12`
4. *(Optional)* In Advanced Settings -> Secrets, add your Gemini API key:
   ```toml
   GEMINI_API_KEY = "your-api-key-here"
   ```
5. Click **Deploy!**

---

## 🏛️ System Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                            MULTI-PLATFORM AD SPEND EXPORTS                        |
|    (Google Ads CSV | Meta Ads CSV | TikTok Ads CSV | Email CSV | Organic SEO CSV)   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        POLARS ZERO-COPY INGESTION PIPELINE                        |
|   - Auto-detection of ad platform column signatures                               |
|   - Fast multi-format date cleaning & currency string normalization                |
|   - Pydantic v2 Contract Validation (`StandardAdRecord`)                          |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                         DUCKDB VECTORIZED SQL ANALYTICS ENGINE                    |
|   - Blended CAC, ROAS, CPA, and Conversion Rate Computation                       |
|   - Window Function Multi-Touch Models (First-Touch, Last-Touch, Linear, Time-Decay)|
+-----------------------------------------------------------------------------------+
                                         |
                       +-----------------+-----------------+
                       |                                   |
                       v                                   v
+----------------------------------------+ +----------------------------------------+
|      GEMINI 3.5 FLASH AI ENGINE        | |       STREAMLIT COMMAND CENTER UI      |
|  - Structured Output via Pydantic v2   | |  - Glassmorphic dark aesthetic (#0B0F19)|
|  - Status-code-first error taxonomy    | |  - Argon2 auth + 1-Click Recruiter Demo |
|  - Automated executive C-suite brief   | |  - Plotly MTA charts & Budget Simulator|
+----------------------------------------+ +----------------------------------------+
                       |                                   |
                       +-----------------+-----------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                     FPDF2 DARK C-SUITE PDF EXECUTIVE BRIEF                        |
+-----------------------------------------------------------------------------------+
```

---

## ✨ Enterprise Features

- **Multi-Platform Ad Ingestion**: Seamless zero-copy CSV parsing for Google Ads, Meta Ads, TikTok Ads, Email Marketing, and Organic SEO exports using **Polars**.
- **Pydantic v2 Data Contracts**: Boundary validation for all ingested marketing records via `StandardAdRecord` and `UnifiedAdDataset`.
- **DuckDB SQL Attribution Engine**: Vectorized window function execution computing **First-Touch**, **Last-Touch**, **Linear**, and **Time-Decay** attribution models alongside Blended CAC, CPA, and ROAS.
- **Gemini 3.5 AI Executive Briefs**: Automated generation of C-suite performance reports using `google-genai` SDK targeting `gemini-3.5-flash` with native Pydantic structured outputs (`MarketingInsightsReport`).
- **Status-Code-First Error Taxonomy**: Resilient AI client handling with telemetry classification (`CAT_QUOTA`, `CAT_AUTH`, `CAT_TIMEOUT`, `CAT_SCHEMA`) and deterministic mock fallback.
- **Argon2 Security & Recruiter Demo Login**: Secure Argon2id password hashing + 1-click **Recruiter Demo Login** for instant sandbox evaluation.
- **Dark Glassmorphic Command-Center UI**: Built with Streamlit, custom CSS (`#0B0F19` dark theme, `#00E5FF` cyan accents), Plotly visualizations, and interactive budget reallocation simulator.
- **FPDF2 Executive PDF Exporter**: Branded executive summary brief generator.

---

## 📂 Repository Structure

```
Marketing-ROI-Tracker/
├── .github/workflows/
│   ├── ci.yml                 # Python 3.12/3.13 + Node 22 LTS CI Runner
│   └── codeql-analysis.yml    # CodeQL Security SAST
├── src/
│   ├── schemas/               # Pydantic v2 validation contracts (`ad_platforms.py`)
│   ├── engine/                # Polars ingestion & DuckDB SQL attribution (`ingestion.py`, `attribution.py`)
│   ├── ai/                    # Gemini 3.5 structured output client (`insights_engine.py`)
│   ├── auth/                  # Argon2 authentication & demo bypass logic (`security.py`)
│   ├── reporting/             # FPDF2 C-suite PDF generator (`pdf_generator.py`)
│   └── ui/                    # Streamlit CSS styles & Plotly components (`styles.py`, `components.py`)
├── tests/                     # Pytest suite with zero external API key requirements
├── app.py                     # Main Streamlit presentation layer
├── pyproject.toml             # Ruff, Mypy, and Pytest configuration
└── requirements.txt           # Core dependencies
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.12 or 3.13
- Git

### 2. Installation
```bash
# Clone repository
git clone https://github.com/Ali-datasmith/Marketing-ROI-Tracker.git
cd Marketing-ROI-Tracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

- **Recruiter Demo Access**: Click **"🚀 1-Click Recruiter Demo Access"** on the login screen.
- **Admin Password**: Default credentials: `admin` / `admin123`.

---

## 🧪 Testing & Code Quality

Run full unit test suite and quality gates locally:

```bash
# Run pytest test suite
pytest

# Run Ruff linter
ruff check .

# Run Mypy strict type checker
mypy src/ --ignore-missing-imports
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
