# ==============================================================================
# app/utils.py - File I/O & CSV Helper Utilities
# ==============================================================================
# This file contains helper functions to read, write, initialize, and serialize
# expense data stored in our CSV file on disk.

# Import Python's built-in 'csv' library, which handles parsing and writing Comma Separated Values.
import csv

# Import our file path (CSV_FILE) and column header list (CSV_COLUMNS) from config.py.
from app.config import CSV_FILE, CSV_COLUMNS


# Define a function to prepare the storage directory and file when the application starts up.
def initialize_csv():
    """Create the data directory and CSV header if necessary."""
    # CSV_FILE.parent gets the directory path where the CSV lives (e.g. '/data').
    # .mkdir() creates that directory on disk.
    # parents=True means create any missing parent folders along the path.
    # exist_ok=True prevents an error if the directory already exists.
    CSV_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Check if the file doesn't exist yet, OR if it exists but is completely empty (0 bytes).
    if not CSV_FILE.exists() or CSV_FILE.stat().st_size == 0:
        # Open the file in write mode ('w') with UTF-8 character encoding.
        # newline="" is recommended by Python docs to prevent extra blank lines on Windows.
        # The 'with' statement ensures the file is automatically closed when the block finishes.
        with CSV_FILE.open("w", newline="", encoding="utf-8") as file:
            # csv.DictWriter lets us write rows using Python dictionaries matching our column names.
            writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
            # Write the first line of the CSV containing the header names (id, title, amount, etc.).
            writer.writeheader()


# Define a function to read and return all rows from the CSV file.
def read_csv():
    """Read all rows from the CSV file."""
    # Ensure the directory and file exist before trying to read from it.
    initialize_csv()

    # Open the CSV file in read mode ('r').
    with CSV_FILE.open("r", newline="", encoding="utf-8") as file:
        # csv.DictReader reads each line and maps each value to its column header as a dictionary.
        # list() converts the reader generator into an in-memory Python list of row dictionaries.
        # Example: [{"id": "1", "title": "Coffee", "amount": "4.50", ...}]
        return list(csv.DictReader(file))


# Define a function to overwrite the CSV with updated data rows.
def write_csv(rows):
    """Replace the CSV contents with the supplied rows."""
    # Ensure the data directory exists.
    initialize_csv()

    # Create a temporary file path with extension '.tmp' (e.g. expenses.tmp).
    # Writing to a temp file first is a safety technique called "atomic write":
    # If the app crashes midway, the original data file remains unharmed and uncorrupted.
    temp_file = CSV_FILE.with_suffix(".tmp")

    # Open the temporary file in write mode ('w').
    with temp_file.open("w", newline="", encoding="utf-8") as file:
        # Initialize a DictWriter configured with our standard column list.
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        # Write the column header row at the top of the file.
        writer.writeheader()
        # Write all the dictionary rows provided in the 'rows' parameter.
        writer.writerows(rows)

    # Atomically replace the old CSV file with the freshly written temp file.
    # On most operating systems, this swap happens instantaneously.
    temp_file.replace(CSV_FILE)


# Define a function to convert raw string values from CSV into proper Python data types.
def serialize_expense(row):
    """Convert CSV string values to API-friendly Python types."""
    # CSV files store everything as text strings (e.g. "1", "25.50").
    # For JSON and API responses, we convert numbers to real int and float types.
    return {
        # Convert string ID "1" into Python integer 1.
        "id": int(row["id"]),
        # Keep title as a string.
        "title": row["title"],
        # Convert string amount "25.50" into Python float 25.5.
        "amount": float(row["amount"]),
        # Keep category as a string.
        "category": row["category"],
        # Keep date string (e.g. "2026-09-25").
        "date": row["date"],
        # row.get("notes", "") safely gets the notes value, defaulting to "" if missing.
        "notes": row.get("notes", ""),
    }
