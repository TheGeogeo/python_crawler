# Web Crawler (SQLite + FastAPI)

A small Python app that:
- Crawls web pages starting from a **seed URL**
- Extracts `<a href>` links and stores them in **SQLite** (no duplicates)
- Runs a **FastAPI** web UI to view collected URLs (clickable)
- Opens the web UI automatically on startup
- Supports **multiple crawler threads** (default: 1)

---

## Requirements
- Python 3.10+ (recommended 3.11/3.12)
- pip

---

## Install

### Linux / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)
```bat
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

(If PowerShell blocks activation)
```bat
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

---

## Run (example)
```bash
python run.py --seed "https://example.com" --threads 4 --delay 0.3
```

Then open (auto-open should happen):
- Home: `http://127.0.0.1:8000/`
- Clickable list: `http://127.0.0.1:8000/urls`
- JSON API: `http://127.0.0.1:8000/api/urls`

Stop with **Ctrl + C**.

---

## Options (quick)
- `--seed URL` (required) : start URL
- `--threads N` (default: 1) : number of crawler threads
- `--delay SECONDS` (default: 0.5) : delay between requests per thread
- `--max-pages N` (default: unlimited) : stop after N processed pages
- `--same-domain-only` (default: off) : restrict crawling to the seed domain
- `--db FILE` (default: crawler.sqlite) : SQLite database file
- `--host HOST` / `--port PORT` (default: 127.0.0.1 / 8000) : web server bind
