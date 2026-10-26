# Expense & Insights API

A REST API that stores personal spending data and answers questions like
"how much did I spend on food this month?"

Built with Python, FastAPI, SQLite and pytest.

## Features
- Add transactions with validation (positive amounts, real dates)
- Filter transactions by date range and category
- Spending reports: by category, by merchant, by month
- Upload a CSV export; new merchants and categories are created automatically
- Bad CSV rows are reported with line numbers while good rows still import
- 10 automated tests

## Run it locally
    python -m venv .venv
    .venv\Scripts\activate
    python -m pip install fastapi "uvicorn[standard]" python-multipart pytest httpx
    cd expense-api
    python setup_db.py
    python -m uvicorn main:app --reload

Then open http://127.0.0.1:8000/docs

## Run the tests
    cd expense-api
    python -m pytest -v

## Endpoints
| Method | Path | What it does |
|---|---|---|
| GET | /transactions | List transactions (filters: start_date, end_date, category) |
| POST | /transactions | Add one transaction |
| POST | /transactions/upload | Import a CSV file |
| GET | /spending/by-category | Totals per category |
| GET | /spending/by-merchant | Totals per merchant |
| GET | /spending/monthly | Totals per month |

## What I learned
- Designing a 3-table schema with foreign keys
- Validating input with Pydantic
- Writing tests against a throwaway database
- Making query ordering deterministic (ties in totals)

## Next
Project 2 will add an AI layer on top of this data.