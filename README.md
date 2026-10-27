
# Expense Tracker API

A RESTful backend application built using Python, FastAPI, Pydantic,
CSV, Pandas, and NumPy to manage expenses and analyze spending patterns.

## Features

- Create, read, update, and delete expenses
- Validate expense data using Pydantic
- Store expenses in CSV format
- Search expenses by category and date range
- Pagination and sorting
- Monthly, daily, and category-wise reports
- Total, average, highest, and lowest expense statistics
- Interactive Swagger API documentation
- Automated API tests with pytest

## Tech Stack

- Python
- FastAPI
- Uvicorn
- Pydantic
- Pandas
- NumPy
- CSV
- Pytest

## Project Structure

```text
expense_tracker_api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── services.py
│   ├── analytics.py
│   ├── utils.py
│   └── config.py
├── data/
│   └── expenses.csv
├── tests/
│   └── test_api.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

Requires Python 3.10 or newer.

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload
```

API base URL:

http://127.0.0.1:8000

Swagger UI:

http://127.0.0.1:8000/docs

ReDoc:

http://127.0.0.1:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /health | Health check |
| POST | /expenses | Create an expense |
| GET | /expenses | List, filter, sort, and paginate |
| GET | /expenses/{expense_id} | Retrieve one expense |
| PUT | /expenses/{expense_id} | Update an expense |
| DELETE | /expenses/{expense_id} | Delete an expense |
| GET | /reports/statistics | Overall statistics |
| GET | /reports/monthly | Monthly summary |
| GET | /reports/category | Category summary |
| GET | /reports/daily | Daily summary |

## Example Request

POST /expenses

```json
{
  "title": "Lunch",
  "amount": 250,
  "category": "Food",
  "date": "2026-09-25",
  "notes": "Office lunch"
}
```

## Filtering and Pagination

```text
GET /expenses?category=Food
GET /expenses?start_date=2026-09-01&end_date=2026-09-30
GET /expenses?sort_by=amount&order=desc
GET /expenses?limit=10&offset=0
```

## Run Tests

```bash
pytest -v
```

## Future Improvements

- SQLite or PostgreSQL persistence
- JWT authentication
- User-specific expenses
- Excel export
- Docker
- Cloud deployment
- CI/CD with GitHub Actions
