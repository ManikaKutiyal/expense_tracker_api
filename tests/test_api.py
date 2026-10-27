# ==============================================================================
# tests/test_api.py - Automated Unit & Integration Tests
# ==============================================================================
# This file tests our FastAPI endpoints automatically using 'pytest'.
# Automated tests ensure code works correctly and prevents bugs when changes are made.

# Import the 'pytest' testing framework.
import pytest
# Import 'TestClient' from FastAPI, which simulates HTTP requests (GET, POST, PUT, DELETE)
# without needing to actually run an external web server.
from fastapi.testclient import TestClient

# Import app modules so we can patch file paths during testing to avoid touching real data.
import app.services as services
import app.utils as utils
# Import the column list from config.
from app.config import CSV_COLUMNS
# Import the FastAPI application instance we defined in main.py.
from app.main import app


# @pytest.fixture is a decorator that creates a reusable setup/teardown environment for tests.
# Pytest automatically passes fixtures to any test function that asks for them by name.
@pytest.fixture
# 'tmp_path' is a built-in pytest fixture that creates a temporary directory isolated for each test.
# 'monkeypatch' is a built-in fixture used to safely modify attributes or functions during testing.
def client(tmp_path, monkeypatch):
    # Create a path for a dummy expenses.csv inside the isolated temporary folder.
    test_csv = tmp_path / "expenses.csv"

    # monkeypatch redirects CSV_FILE in utils to point to our temporary file instead of the real data file.
    monkeypatch.setattr(utils, "CSV_FILE", test_csv)
    # Ensure services.py uses the patched utils functions and paths.
    monkeypatch.setattr(services, "read_csv", utils.read_csv)
    monkeypatch.setattr(services, "write_csv", utils.write_csv)

    # Initialize the temporary CSV file with headers before running tests.
    utils.initialize_csv()

    # Create an HTTP test client connected to our FastAPI app.
    with TestClient(app) as test_client:
        # 'yield' hands the test_client over to the test function.
        # After the test finishes, control returns here for any cleanup.
        yield test_client


# Helper function to generate a sample expense dictionary with sensible defaults for tests.
def sample_expense(title="Lunch", amount=250, category="Food"):
    return {
        "title": title,
        "amount": amount,
        "category": category,
        "date": "2026-09-25",
        "notes": "Test expense",
    }


# Test to verify that the health check endpoint returns 200 OK and status 'ok'.
def test_health(client):
    # Send a GET request to the '/health' endpoint.
    response = client.get("/health")

    # 'assert' checks if an expression is True; if False, pytest fails the test.
    # Verify the HTTP response status code is 200 (OK).
    assert response.status_code == 200
    # Verify the JSON response body contains {"status": "ok"}.
    assert response.json()["status"] == "ok"


# Test creating a new expense through POST /expenses.
def test_create_expense(client):
    # Send a POST request to '/expenses' with JSON payload from sample_expense().
    response = client.post(
        "/expenses",
        json=sample_expense(),
    )

    # Check that HTTP 201 Created was returned.
    assert response.status_code == 201
    # Check that the first expense was assigned ID 1.
    assert response.json()["id"] == 1
    # Check that the title in the response matches "Lunch".
    assert response.json()["title"] == "Lunch"


# Test fetching the list of expenses through GET /expenses.
def test_list_expenses(client):
    # First, insert one expense so there is data to list.
    client.post("/expenses", json=sample_expense())

    # Send a GET request to '/expenses'.
    response = client.get("/expenses")

    # Verify response is 200 OK.
    assert response.status_code == 200
    # Verify total count in metadata is 1.
    assert response.json()["total"] == 1
    # Verify the items list contains exactly 1 element.
    assert len(response.json()["items"]) == 1


# Test retrieving a single expense by its unique ID.
def test_get_expense_by_id(client):
    # Insert an expense (which gets ID 1).
    client.post("/expenses", json=sample_expense())

    # Send a GET request for expense with ID 1.
    response = client.get("/expenses/1")

    # Check response is 200 OK.
    assert response.status_code == 200
    # Check that the expense amount is 250.
    assert response.json()["amount"] == 250


# Test requesting an expense ID that does not exist.
def test_missing_expense(client):
    # Send a GET request for non-existent ID 999.
    response = client.get("/expenses/999")

    # Verify that the API returns HTTP 404 (Not Found).
    assert response.status_code == 404


# Test updating an existing expense via PUT /expenses/{id}.
def test_update_expense(client):
    # Insert initial expense.
    client.post("/expenses", json=sample_expense())

    # Prepare updated data (changing title to "Dinner" and amount to 350).
    updated = sample_expense(
        title="Dinner",
        amount=350,
        category="Food",
    )

    # Send a PUT request to update expense with ID 1.
    response = client.put("/expenses/1", json=updated)

    # Verify update succeeded with 200 OK.
    assert response.status_code == 200
    # Verify that new title is "Dinner".
    assert response.json()["title"] == "Dinner"
    # Verify that new amount is 350.
    assert response.json()["amount"] == 350


# Test deleting an expense via DELETE /expenses/{id}.
def test_delete_expense(client):
    # Insert an expense to be deleted.
    client.post("/expenses", json=sample_expense())

    # Send DELETE request for expense with ID 1.
    response = client.delete("/expenses/1")

    # Verify deletion returned 200 OK.
    assert response.status_code == 200
    # Verify that requesting the deleted expense now returns 404 Not Found.
    assert client.get("/expenses/1").status_code == 404


# Test that creating an expense with a negative amount is rejected.
def test_invalid_amount(client):
    # Attempt to post an expense with amount -100.
    response = client.post(
        "/expenses",
        json=sample_expense(amount=-100),
    )

    # Verify that Pydantic validation rejects it with HTTP 422 Unprocessable Entity.
    assert response.status_code == 422


# Test that creating an expense with a missing required field (title) is rejected.
def test_missing_required_field(client):
    # Create sample dictionary.
    expense = sample_expense()
    # Delete the mandatory 'title' key.
    del expense["title"]

    # Post the incomplete dictionary.
    response = client.post("/expenses", json=expense)

    # Verify that missing required field produces HTTP 422 Unprocessable Entity.
    assert response.status_code == 422


# Test that sending an invalid date string format is rejected.
def test_invalid_date(client):
    # Post with a nonsense date string instead of YYYY-MM-DD.
    response = client.post(
        "/expenses",
        json={
            **sample_expense(),
            "date": "not-a-date",
        },
    )

    # Verify that invalid date format produces HTTP 422 Unprocessable Entity.
    assert response.status_code == 422


# Test filtering expenses by category using URL query parameter.
def test_category_filter(client):
    # Insert an expense with category "Food".
    client.post("/expenses", json=sample_expense())
    # Insert a second expense with category "Travel".
    client.post(
        "/expenses",
        json=sample_expense(
            title="Metro",
            amount=80,
            category="Travel",
        ),
    )

    # Request only expenses in category "Food".
    response = client.get("/expenses?category=Food")

    # Verify 200 OK status.
    assert response.status_code == 200
    # Verify that total count returned is only 1 (only the Food expense).
    assert response.json()["total"] == 1
    # Verify the returned item belongs to the "Food" category.
    assert response.json()["items"][0]["category"] == "Food"
