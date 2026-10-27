# ==============================================================================
# app/main.py - FastAPI Application & HTTP Endpoints
# ==============================================================================
# This is the entry point of the web API application.
# It sets up the FastAPI app, configures error handlers, and defines all REST API endpoints
# for managing expenses and viewing analytical reports.

# Import Python's built-in 'csv' module for catching CSV-specific file errors.
import csv
# Import Python's built-in 'logging' module to print informative messages and debug info to the console.
import logging
# Import 'date' type from datetime for parsing and validating calendar date parameters.
from datetime import date
# Import 'Optional' type hint to indicate query parameters that the client doesn't have to provide.
from typing import Optional

# Import FastAPI building blocks:
# - FastAPI: The central class used to create our web API application.
# - HTTPException: Exception class used to return error responses with specific HTTP status codes (e.g., 404).
# - Query: Helper function used to define validation rules, defaults, and descriptions for URL query parameters.
# - Request: Represents the incoming HTTP request from a client.
from fastapi import FastAPI, HTTPException, Query, Request
# Import JSONResponse to send custom JSON payloads with specific HTTP status codes.
from fastapi.responses import JSONResponse

# Import analytics functions from our analytics module to generate spending reports.
from app.analytics import (
    get_category_summary,
    get_daily_summary,
    get_monthly_summary,
    get_statistics,
)
# Import Pydantic models from models.py for request validation and response formatting.
from app.models import ExpenseCreate, ExpenseResponse, ExpenseUpdate
# Import service functions from services.py for CRUD database/file operations.
from app.services import (
    create_expense,
    delete_expense,
    get_all_expenses,
    get_expense_by_id,
    update_expense,
)
# Import utility to initialize our storage file on startup.
from app.utils import initialize_csv

# Configure Python's root logger to output INFO-level log messages and above.
logging.basicConfig(level=logging.INFO)
# Create a logger instance specifically named after the current module (__name__).
logger = logging.getLogger(__name__)

# Create the FastAPI application instance.
# The metadata passed here (title, description, version) powers the automatic Swagger UI docs at '/docs'.
app = FastAPI(
    title="Expense Tracker API",
    description=(
        "A REST API for managing expenses and generating "
        "spending analytics using FastAPI, CSV, Pandas, and NumPy."
    ),
    version="1.0.0",
)


# @app.on_event("startup") is a decorator that tells FastAPI to run this function when the server starts up.
@app.on_event("startup")
def startup():
    # Make sure the 'data/' directory and 'expenses.csv' file exist with proper headers before requests arrive.
    initialize_csv()


# Exception handler for OS-level file system errors (e.g. disk permission denied, disk full).
# When an OSError occurs inside any endpoint, this function catches it automatically.
@app.exception_handler(OSError)
async def handle_storage_error(request: Request, exc: OSError):
    # Log the exact error and traceback in the server console for developers to inspect.
    logger.exception("Storage error while handling %s", request.url.path)
    # Return a safe, clean 500 Internal Server Error JSON response to the client.
    return JSONResponse(
        status_code=500,
        content={"detail": "Unable to access expense storage"},
    )


# Exception handler for CSV parsing errors (e.g. corrupted file lines).
@app.exception_handler(csv.Error)
async def handle_csv_error(request: Request, exc: csv.Error):
    # Log the CSV parsing error in the server console.
    logger.exception("CSV error while handling %s", request.url.path)
    # Return a clean 500 error response so raw tracebacks are never exposed to the client.
    return JSONResponse(
        status_code=500,
        content={"detail": "Unable to process expense storage"},
    )


# -------------------- GENERAL & HEALTH ENDPOINTS --------------------

# @app.get("/") defines a route that responds to HTTP GET requests sent to the root URL ("/").
@app.get("/")
def home():
    # Return a welcoming message and useful links to Swagger documentation and health check.
    return {
        "message": "Welcome to Expense Tracker API",
        "docs": "/docs",
        "health": "/health",
    }


# Health check endpoint used by monitoring tools, load balancers, or uptime checks.
@app.get("/health")
def health_check():
    # Return a simple JSON response confirming the server is alive and functioning.
    return {"status": "ok"}


# -------------------- CRUD ENDPOINTS (EXPENSES) --------------------

# @app.post creates an endpoint for HTTP POST requests to create a new expense.
# - "/expenses": The URL path.
# - response_model=ExpenseResponse: Enforces that outgoing data matches ExpenseResponse schema.
# - status_code=201: Sets HTTP 201 Created (standard for successful resource creation).
# - tags=["Expenses"]: Groups this endpoint under the "Expenses" section in Swagger docs.
@app.post(
    "/expenses",
    response_model=ExpenseResponse,
    status_code=201,
    tags=["Expenses"],
)
# The 'expense: ExpenseCreate' parameter tells FastAPI to read the JSON body from the request
# and validate it automatically using our Pydantic ExpenseCreate schema.
def add_expense(expense: ExpenseCreate):
    # Pass the validated expense data to the service layer to save it and return the new expense.
    return create_expense(expense)


# @app.get defines an endpoint to list expenses with optional filtering, sorting, and pagination.
@app.get("/expenses", tags=["Expenses"])
def list_expenses(
    # 'category' is an optional query parameter in the URL (e.g. ?category=Food).
    # min_length=1 prevents clients from passing empty query strings like ?category=.
    category: Optional[str] = Query(default=None, min_length=1),

    # 'start_date' is an optional query parameter for filtering from a date (e.g. ?start_date=2026-01-01).
    start_date: Optional[date] = None,

    # 'end_date' is an optional query parameter for filtering up to a date (e.g. ?end_date=2026-12-31).
    end_date: Optional[date] = None,

    # 'sort_by' defines which column to sort by. Regex pattern restricts allowed values for security.
    sort_by: str = Query(
        default="date",
        pattern="^(date|amount|title|category|id)$",
    ),

    # 'order' defines sort direction: 'asc' (ascending) or 'desc' (descending).
    order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),

    # 'limit' controls pagination page size (minimum 1, maximum 500).
    limit: int = Query(default=100, ge=1, le=500),

    # 'offset' controls pagination starting index (must be greater than or equal to 0).
    offset: int = Query(default=0, ge=0),
):
    # Validate that start_date does not come chronologically after end_date.
    if start_date and end_date and start_date > end_date:
        # If invalid, immediately raise an HTTP 400 Bad Request error with explanation.
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be after end_date",
        )

    # Delegate the retrieval, filtering, sorting, and slicing to our service function.
    return get_all_expenses(
        category=category,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )


# Endpoint to fetch a single expense by its unique ID.
# {expense_id} is a URL path parameter (e.g. /expenses/5).
@app.get(
    "/expenses/{expense_id}",
    response_model=ExpenseResponse,
    tags=["Expenses"],
)
# FastAPI automatically extracts 'expense_id' from the URL and converts it into an integer.
def read_expense(expense_id: int):
    # Look up the expense with this ID in the CSV file.
    expense = get_expense_by_id(expense_id)

    # If no expense exists with this ID:
    if expense is None:
        # Raise an HTTP 404 Not Found error with a descriptive message.
        raise HTTPException(
            status_code=404,
            detail="Expense not found",
        )

    # If found, return the expense data (FastAPI formats it according to ExpenseResponse).
    return expense


# Endpoint to update an existing expense using HTTP PUT (replace/overwrite).
@app.put(
    "/expenses/{expense_id}",
    response_model=ExpenseResponse,
    tags=["Expenses"],
)
# Accepts the integer ID from the URL path, and the replacement data from the request JSON body.
def edit_expense(expense_id: int, expense: ExpenseUpdate):
    # Call the service layer to perform the update.
    updated = update_expense(expense_id, expense)

    # If the ID did not exist to be updated:
    if updated is None:
        # Return an HTTP 404 Not Found error.
        raise HTTPException(
            status_code=404,
            detail="Expense not found",
        )

    # Return the newly updated expense.
    return updated


# Endpoint to delete an existing expense using HTTP DELETE.
@app.delete("/expenses/{expense_id}", tags=["Expenses"])
# Accepts the integer ID from the URL path.
def remove_expense(expense_id: int):
    # Call the service layer to delete the expense.
    deleted = delete_expense(expense_id)

    # If delete_expense returned False, the expense wasn't found in storage.
    if not deleted:
        # Return an HTTP 404 Not Found error.
        raise HTTPException(
            status_code=404,
            detail="Expense not found",
        )

    # Return a success confirmation message including the deleted ID.
    return {
        "message": "Expense deleted successfully",
        "id": expense_id,
    }


# -------------------- REPORTING & ANALYTICS ENDPOINTS --------------------

# Endpoint to get overall summary statistics (total, average, highest, lowest, daily average).
@app.get("/reports/statistics", tags=["Reports"])
def expense_statistics():
    # Call analytics module to compute statistical metrics using NumPy and Pandas.
    return get_statistics()


# Endpoint to get monthly spending breakdown (e.g., {"2026-09": 450.00, "2026-10": 210.50}).
@app.get("/reports/monthly", tags=["Reports"])
def monthly_report():
    # Call analytics module to aggregate expenses by month.
    return get_monthly_summary()


# Endpoint to get category spending breakdown (e.g., {"Food": 320.00, "Travel": 150.00}).
@app.get("/reports/category", tags=["Reports"])
def category_report():
    # Call analytics module to aggregate expenses by category.
    return get_category_summary()


# Endpoint to get daily spending breakdown (e.g., {"2026-09-25": 45.00, "2026-09-26": 80.00}).
@app.get("/reports/daily", tags=["Reports"])
def daily_report():
    # Call analytics module to aggregate expenses by individual day.
    return get_daily_summary()
