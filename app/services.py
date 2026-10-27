# ==============================================================================
# app/services.py - Business Logic & Data Operations
# ==============================================================================
# This file contains the core "business logic" of the application.
# It acts as a middle layer between the API routes (main.py) and the CSV storage (utils.py).
# Keeping business logic separate makes code easier to test, maintain, and reuse.

# Import 'date' type from Python standard library datetime to work with dates.
from datetime import date
# Import 'Optional' from typing to indicate a parameter can be of that type or None.
from typing import Optional

# Import the predefined CSV column header list from our config module.
from app.config import CSV_COLUMNS
# Import Pydantic models for creating and updating expenses.
from app.models import ExpenseCreate, ExpenseUpdate
# Import helper functions to read from CSV, write to CSV, and convert data types.
from app.utils import read_csv, write_csv, serialize_expense


# Define a function to retrieve expenses with filtering, sorting, and pagination.
def get_all_expenses(
    category: Optional[str] = None,    # Optional filter: category name (e.g. "Food")
    start_date: Optional[date] = None, # Optional filter: only expenses on or after this date
    end_date: Optional[date] = None,   # Optional filter: only expenses on or before this date
    sort_by: str = "date",             # Field to sort by: "date", "amount", "title", "category", "id"
    order: str = "desc",               # Sort direction: "asc" (ascending) or "desc" (descending)
    limit: int = 100,                  # Pagination: maximum number of items to return
    offset: int = 0,                   # Pagination: number of items to skip from the beginning
):
    # Read raw CSV rows and convert each row's string values into Python types (int, float, etc.).
    # This is a Python 'list comprehension' that loops through each row and transforms it.
    rows = [serialize_expense(row) for row in read_csv()]

    # If the caller requested filtering by category:
    if category:
        # Keep only the rows whose category matches the requested category.
        # .casefold() performs aggressive lowercase comparison (better than .lower() for Unicode).
        rows = [
            row for row in rows
            if row["category"].casefold() == category.casefold()
        ]

    # If the caller specified a start date filter:
    if start_date:
        # date.fromisoformat parses a "YYYY-MM-DD" string into a date object so we can compare using '>='.
        rows = [
            row for row in rows
            if date.fromisoformat(row["date"]) >= start_date
        ]

    # If the caller specified an end date filter:
    if end_date:
        # Keep only rows where the expense date is on or before the end date ('<=').
        rows = [
            row for row in rows
            if date.fromisoformat(row["date"]) <= end_date
        ]

    # Determine which attribute to use when sorting rows.
    # 'lambda row: ...' is an anonymous inline function that extracts the sort key from each row.
    if sort_by == "amount":
        # Sort by numeric amount (e.g. 5.0, 12.50, 100.0)
        key = lambda row: row["amount"]
    elif sort_by == "title":
        # Sort alphabetically by title, ignoring uppercase/lowercase differences
        key = lambda row: row["title"].casefold()
    elif sort_by == "category":
        # Sort alphabetically by category name
        key = lambda row: row["category"].casefold()
    elif sort_by == "id":
        # Sort numerically by unique ID number
        key = lambda row: row["id"]
    else:
        # Default fallback: sort chronologically by date string "YYYY-MM-DD"
        key = lambda row: row["date"]

    # Sort the rows in place using Python's Timsort algorithm.
    # reverse=True if order is "desc" (highest/latest first), False if "asc" (lowest/earliest first).
    rows.sort(key=key, reverse=(order == "desc"))

    # Count the total number of items that matched our filters (before pagination slicing).
    total = len(rows)

    # Slice the list to implement pagination: skip 'offset' rows and take up to 'limit' rows.
    # Example: offset=0, limit=10 takes rows[0:10] (the first 10 items).
    items = rows[offset:offset + limit]

    # Return a dictionary containing pagination metadata along with the sliced items.
    return {
        "total": total,     # Total count of matching expenses
        "limit": limit,     # Page size requested
        "offset": offset,   # Starting index
        "items": items,     # List of expenses for this page
    }


# Define a function to search for a single expense by its ID number.
def get_expense_by_id(expense_id: int):
    # Loop through each row in the CSV file one by one.
    for row in read_csv():
        # Check if the row's ID matches the requested integer ID.
        if int(row["id"]) == expense_id:
            # If found, convert the row to Python types and return it immediately.
            return serialize_expense(row)

    # If the loop finishes without finding a match, return None (meaning not found).
    return None


# Define a function to add a new expense record to the CSV file.
def create_expense(expense: ExpenseCreate):
    # Read the current list of rows from the CSV file.
    rows = read_csv()

    # Calculate the next unique ID:
    # Generator expression (int(row["id"]) for row in rows) extracts all existing IDs.
    # max(..., default=0) finds the highest ID currently in use (or 0 if file is empty).
    # Adding +1 ensures every new expense gets a strictly increasing, unique ID.
    next_id = max(
        (int(row["id"]) for row in rows),
        default=0,
    ) + 1

    # Build a dictionary for the new expense record.
    # 'id': next_id assigns the generated ID.
    # **expense.model_dump(mode="json") unrolls Pydantic model fields into key-value pairs.
    new_expense = {
        "id": next_id,
        **expense.model_dump(mode="json"),
    }

    # Format the new expense dictionary into a row dictionary with string values for CSV storage.
    rows.append({
        column: str(new_expense[column])
        for column in CSV_COLUMNS
    })

    # Save the updated rows list back to the CSV file on disk.
    write_csv(rows)

    # Return the newly created expense object (with its assigned ID) back to the caller.
    return new_expense


# Define a function to update an existing expense identified by its ID.
def update_expense(expense_id: int, expense: ExpenseUpdate):
    # Read all rows from the CSV file.
    rows = read_csv()
    # Initialize updated_expense tracker variable to None.
    updated_expense = None

    # Loop through all rows to find the one with the target ID.
    for row in rows:
        # Check if this row's ID matches the ID we want to update.
        if int(row["id"]) == expense_id:
            # Build the updated dictionary preserving the original ID.
            updated_expense = {
                "id": expense_id,
                **expense.model_dump(mode="json"),
            }

            # Update all columns in this CSV row with the new string values.
            for column in CSV_COLUMNS:
                row[column] = str(updated_expense[column])

            # Stop searching the rest of the file since we found and updated the row.
            break

    # If no row matched the given ID, return None to signal that it wasn't found.
    if updated_expense is None:
        return None

    # Write the modified list of rows back to the CSV file.
    write_csv(rows)

    # Return the updated expense record.
    return updated_expense


# Define a function to delete an expense by its ID number.
def delete_expense(expense_id: int):
    # Read all rows from the CSV file.
    rows = read_csv()

    # Create a new list containing all rows EXCEPT the one with the matching ID.
    filtered_rows = [
        row for row in rows
        if int(row["id"]) != expense_id
    ]

    # If the length didn't change, no row was removed (the ID didn't exist).
    if len(filtered_rows) == len(rows):
        # Return False to indicate nothing was deleted.
        return False

    # Write the filtered list (without the deleted row) back to disk.
    write_csv(filtered_rows)

    # Return True to indicate successful deletion.
    return True
