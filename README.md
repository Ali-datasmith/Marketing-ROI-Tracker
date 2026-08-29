# ⚡ MARKETING ROI ENGINE: Enterprise B2B Multi-Touch Attribution & Budget Optimization Engine

[![Enterprise CI Pipeline](https://github.com/Ali-datasmith/Marketing-ROI-Tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/Ali-datasmith/Marketing-ROI-Tracker/actions/workflows/ci.yml)
[![CodeQL Security SAST](https://github.com/Ali-datasmith/Marketing-ROI-Tracker/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/Ali-datasmith/Marketing-ROI-Tracker/actions/workflows/codeql-analysis.yml)
[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Node Baseline](https://img.shields.io/badge/node-22%20LTS-green.svg)](https://nodejs.org/)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked](https://img.shields.io/badge/mypy-strict-brightgreen.svg)](https://mypy-lang.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🏛️ Executive Summary & System Overview

**MARKETING ROI ENGINE (v2.0 Enterprise Edition)** is a production-grade, B2B Multi-Touch Attribution (MTA) & Budget Optimization Engine. Engineered to replace basic legacy marketing scripts with an enterprise analytics architecture, the platform synthesizes raw multi-platform ad spend exports (Google Ads, Meta Ads, TikTok Ads, Email Marketing, Organic SEO) into actionable C-suite revenue attribution intelligence.

### Key Architectural Highlights
- **Zero-Copy Ingestion**: Polars-powered CSV ingestion pipeline with automated platform signature detection, date string normalization, and currency string cleaning.
- **Vectorized SQL Analytics**: In-memory DuckDB engine executing window functions for real-time calculation of **First-Touch**, **Last-Touch**, **Linear**, and **Time-Decay** attribution models alongside Blended CAC, CPA, and ROAS.
- **Pydantic v2 Contract Validation**: Strict boundary schema contracts (`StandardAdRecord`, `UnifiedAdDataset`) ensuring structural integrity before DuckDB query execution.
- **Gemini 3.5 AI Synthesis Engine**: Generative executive briefing powered by `google-genai` SDK targeting `gemini-3.5-flash` with native Pydantic structured JSON outputs (`MarketingInsightsReport`) and status-code-first error taxonomy (`CAT_QUOTA`, `CAT_AUTH`, `CAT_TIMEOUT`, `CAT_SCHEMA`).
- **Argon2 Security Access Gate**: Enterprise Argon2id password hashing + 1-click **Recruiter Demo Access** for read-only sandbox evaluation.
- **Glassmorphic Command Center UI**: Custom dark theme (`#0B0F19` background, `#00E5FF` cyan accents) featuring emergent lighting panels, Plotly MTA comparison charts, interactive diminishing-returns budget simulator, and FPDF2 dark executive PDF generation.

---

## 📐 End-to-End System Architecture

```
+-----------------------------------------------------------------------------------+
|                            MULTI-PLATFORM AD SPEND EXPORTS                        |
|    (Google Ads CSV | Meta Ads CSV | TikTok Ads CSV | Email CSV | Organic SEO CSV)   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        POLARS ZERO-COPY INGESTION PIPELINE                        |
|   - Auto-detection of platform signatures (Google, Meta, TikTok, Email, SEO)      |
|   - Fast multi-format date parsing (%Y-%m-%d, %m/%d/%Y, %d-%b-%Y, etc.)           |
|   - Currency string normalization & coercion                                      |
|   - Pydantic v2 Contract Validation (`StandardAdRecord`)                          |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                         DUCKDB VECTORIZED SQL ANALYTICS ENGINE                    |
|   - Blended CAC, ROAS, CPA, & Conversion Rate aggregation                         |
|   - Window Function Multi-Touch Models (First-Touch, Last-Touch, Linear, Time-Decay)|
+-----------------------------------------------------------------------------------+
                                         |
                       +-----------------+-----------------+
                       |                                   |
                       v                                   v
+----------------------------------------+ +----------------------------------------+
|      GEMINI 3.5 FLASH AI ENGINE        | |       STREAMLIT COMMAND CENTER UI      |
|  - Structured Output via Pydantic v2   | |  - Emergent glassmorphic dark theme   |
|  - Status-code-first error taxonomy    | |  - Argon2 auth + 1-Click Recruiter Demo |
|  - C-suite executive performance report| |  - Interactive Budget Simulator        |
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

## 🔀 Multi-Touch Attribution Models

The DuckDB SQL engine executes four distinct attribution methodologies across marketing touchpoints:

| Model | Formula / Logic | Business Use Case |
| :--- | :--- | :--- |
| **First-Touch** | Attributes 100% credit to the initial acquisition channel (`DENSE_RANK() OVER (ORDER BY first_seen ASC)`) | Evaluating top-of-funnel brand awareness & demand generation. |
| **Last-Touch** | Attributes 100% credit to the final converting channel (`DENSE_RANK() OVER (ORDER BY last_seen DESC)`) | Measuring bottom-of-funnel direct conversion efficiency. |
| **Linear** | Distributes credit equally across all touchpoints in the journey | Balanced evaluation for long B2B sales cycles with multiple touchpoints. |
| **Time-Decay** | Applies exponential decay weighting (`0.85 ^ days_before_conversion`) favoring recent interactions | Ideal for multi-week lead-to-opportunity conversions. |

---

## 📁 Repository Directory Structure

```
Marketing-ROI-Tracker/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Node 22 LTS + Python 3.12/3.13 matrix runner
│       └── codeql-analysis.yml    # CodeQL Security SAST static analysis
├── src/
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── ad_platforms.py        # Pydantic v2 boundary models (StandardAdRecord)
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── ingestion.py           # Polars zero-copy CSV parsing & platform detector
│   │   └── attribution.py         # DuckDB SQL vectorized MTA window functions
│   ├── ai/
│   │   ├── __init__.py
│   │   └── insights_engine.py     # Gemini 3.5 Flash client with Pydantic structured output
│   ├── auth/
│   │   ├── __init__.py
│   │   └── security.py            # Argon2id password hashing & Recruiter Demo permissions
│   ├── reporting/
│   │   ├── __init__.py
│   │   └── pdf_generator.py       # FPDF2 dark-themed executive brief generator
│   └── ui/
│       ├── __init__.py
│       ├── styles.py              # Emergent glassmorphic CSS theme
│       └── components.py          # Plotly MTA charts & budget simulator
├── tests/
│   ├── __init__.py
│   ├── test_schemas.py            # Pydantic contract unit tests
│   ├── test_ingestion.py          # Polars ingestion & platform signature tests
│   ├── test_attribution.py        # DuckDB SQL attribution model tests
│   └── test_security_reporting.py # Argon2 auth, AI fallback, & FPDF2 tests
├── data/                          # Enterprise sample CSV datasets
├── app.py                         # Streamlit presentation layer & Cloud entrypoint
├── pyproject.toml                 # Ruff, Mypy, and Pytest configuration
├── requirements.txt               # Production Python dependencies
└── README.md                      # Architecture & operational documentation
```

---

## 💻 Local Setup & Execution Guide

### 1. Requirements
- **Python**: 3.12 or 3.13
- **Git**

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/Ali-datasmith/Marketing-ROI-Tracker.git
cd Marketing-ROI-Tracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch Application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

- **Recruiter Demo Access**: Click **"🚀 1-Click Recruiter Demo Access"** on the Executive Access Gate to bypass credentials with read-only sandbox permissions.
- **Admin Password**: `admin` / `admin123`.

---

## ☁️ Streamlit Community Cloud Deployment

The repository includes dynamic `sys.path` resolution for `src/` inside `app.py` for zero-configuration Streamlit Community Cloud deployment:

1. Push your repository to GitHub.
2. Sign in to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository with the following settings:
   - **Main file path**: `app.py`
   - **Python version**: `3.12`
4. *(Optional)* Add your Gemini API key in **Advanced Settings -> Secrets**:
   ```toml
   GEMINI_API_KEY = "your-actual-gemini-api-key"
   ```
5. Deploy!

---

## 🧪 Testing, Quality Gates & Security Scans

The repository maintains 100% test passing rates and zero-warning linter compliance.

```bash
# Execute Pytest Unit Test Suite
pytest

# Execute Ruff Linter
ruff check .

# Execute Mypy Strict Type Checking
mypy src/ --ignore-missing-imports
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
