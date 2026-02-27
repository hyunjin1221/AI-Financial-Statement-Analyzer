# AI Financial Statement Analyzer

Free, local-first financial filing analysis app built with Streamlit, SEC EDGAR APIs, and Ollama.

## Overview
This project analyzes SEC 10-K and 10-Q filings and produces:
- Filing section extraction (Business, Risk Factors, MD&A)
- Financial ratio calculations from SEC XBRL company facts
- Optional AI narrative insights (revenue trends, debt risk, red flags, management commentary)
- Optional SIC-based peer benchmark comparison
- Investment-style summary (research only, not advice)
- Downloadable Markdown report + optional local report history

## Key Features
- Free-only stack: no paid APIs required
- SEC fair-access aware client (headers, retries, rate limiting)
- Structured AI extraction with normalized JSON schema
- Evidence span traceability (`evidence_spans`) for extracted AI quotes
- Ratio quality flags (`ok`, `missing_data`, `unstable_denominator`)
- Cached SEC fetches for faster Streamlit reruns
- Tested pipeline with unit + mocked integration tests

## Tech Stack
- Python
- Streamlit
- SEC EDGAR APIs
- Pandas + Plotly
- Ollama (local LLM)
- Pytest

## Project Structure
```text
app/
  main.py
  config.py
  services/
  models/
  utils/

tests/
notes/
requirements.txt
README.md
```

## Quick Start
```bash
cd "/Users/hyunjinyu/Projects/AI Financial Statement Analyzer"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with your SEC contact identity:
```bash
SEC_USER_AGENT=YourName your_email@example.com
```

## Ollama Setup (for AI extraction)
```bash
ollama pull llama3.1:8b
```

If you prefer a smaller model, you can use one and update `.env`:
```bash
OLLAMA_MODEL=llama3.2:3b
```

## Run the App
```bash
streamlit run app/main.py
```

Open: [http://localhost:8501](http://localhost:8501)

## Streamlit Workflow
Sidebar controls:
- `Ticker`
- `Preferred filing` (`10-K` or `10-Q`)
- `Run local AI extraction (Ollama)`
- `Run peer benchmark (slower)`
- `Save report to local history`

Main outputs:
- Company + filing metadata
- Section extraction with source spans
- Ratio table + chart
- AI insights JSON + evidence spans (if enabled)
- Peer comparison table + delta chart (if enabled)
- Summary + markdown report download

## Testing
```bash
pytest -q
```

Current status: all tests passing.

## Free-Only Design
- SEC public filings + XBRL data
- Local LLM inference via Ollama
- Open-source Python libraries
- No paid data providers or paid model APIs required

## Disclaimer
This project is for educational and research purposes only.
It is not financial or investment advice.
