# Import NumPy, the industry standard Python library for fast numerical and mathematical calculations.
# 'as np' is the universal convention for referencing numpy.
import numpy as np
# Import Pandas, the premier Python data analysis library that provides DataFrames (tables).
# 'as pd' is the universal convention for referencing pandas.
import pandas as pd

# Import the read_csv helper from utils to fetch the raw data rows.
from app.utils import read_csv


# Helper function to load CSV data into a typed Pandas DataFrame (like an in-memory SQL/Excel table).
def get_dataframe():
    # Fetch all records from the CSV file as a list of dictionaries.
    rows = read_csv()

    # Define the column names in order for the DataFrame.
    columns = ["id", "title", "amount", "category", "date", "notes"]
    # Create a Pandas DataFrame from the rows and explicit column names.
    df = pd.DataFrame(rows, columns=columns)

    # Check if the DataFrame is empty (no expense records exist yet).
    if df.empty:
        # If empty, return the empty DataFrame early to prevent calculation errors.
        return df

    # Convert the "id" column from text strings (e.g. "1") into standard integers.
    df["id"] = df["id"].astype(int)
    # Convert "amount" column from strings to numeric floats; raise an error if any invalid value is found.
    df["amount"] = pd.to_numeric(df["amount"], errors="raise")
    # Convert "date" column strings into true Pandas datetime objects so we can do date-based operations.
    df["date"] = pd.to_datetime(df["date"], errors="raise")

    # Return the clean, typed DataFrame ready for analysis.
    return df


# Compute key summary metrics (total, average, highest, lowest, count, average daily spending).
def get_statistics():
    # Load the parsed expenses DataFrame.
    df = get_dataframe()

    # If there are no expenses in the system, return default zero/null metrics.
    if df.empty:
        return {
            "total": 0.0,
            "average": 0.0,
            "highest": None,
            "lowest": None,
            "count": 0,
            "average_daily_expense": 0.0,
        }

    # Extract the "amount" column as a 1D NumPy array of 64-bit floating point numbers for fast math.
    amounts = df["amount"].to_numpy(dtype=float)

    # Group expenses by calendar date (df["date"].dt.date) and calculate total spending for each distinct day.
    daily_totals = df.groupby(df["date"].dt.date)["amount"].sum()

    # Return a dictionary of summary statistics:
    return {
        # np.sum adds up all expense amounts; round to 2 decimal places (cents/pence).
        "total": round(float(np.sum(amounts)), 2),
        # np.mean computes the arithmetic mean (average) per expense.
        "average": round(float(np.mean(amounts)), 2),
        # np.max finds the single largest expense amount.
        "highest": round(float(np.max(amounts)), 2),
        # np.min finds the smallest expense amount.
        "lowest": round(float(np.min(amounts)), 2),
        # len(df) counts the total number of recorded expenses.
        "count": int(len(df)),
        # daily_totals.mean() computes the average money spent per active day.
        "average_daily_expense": round(
            float(daily_totals.mean()), 2
        ),
    }


# Calculate total spending grouped by month (e.g. "2026-09": 540.25).
def get_monthly_summary():
    # Load the parsed expenses DataFrame.
    df = get_dataframe()

    # If there are no expenses, return an empty dictionary.
    if df.empty:
        return {}

    # Create a new temporary column "month" formatted as "YYYY-MM" (e.g. "2026-09").
    # .dt gives access to datetime properties, and .strftime formats the date to text.
    df["month"] = df["date"].dt.strftime("%Y-%m")

    # Group all rows having the same month and calculate the sum of amounts for each month.
    summary = df.groupby("month")["amount"].sum()

    # Return a dictionary where the keys are months and values are rounded totals.
    # Uses a dictionary comprehension: {key: value for key, value in iterable}
    return {
        month: round(float(amount), 2)
        for month, amount in summary.items()
    }


# Calculate total spending grouped by category (e.g. "Food": 150.00, "Travel": 80.00).
def get_category_summary():
    # Load the parsed expenses DataFrame.
    df = get_dataframe()

    # If there are no expenses, return an empty dictionary.
    if df.empty:
        return {}

    # Group all rows by the "category" column and sum the "amount" column for each group.
    summary = df.groupby("category")["amount"].sum()

    # Convert the resulting Pandas Series into a clean Python dictionary with 2-decimal rounded floats.
    return {
        category: round(float(amount), 2)
        for category, amount in summary.items()
    }


# Calculate total spending grouped by individual day (e.g. "2026-09-25": 45.50).
def get_daily_summary():
    # Load the parsed expenses DataFrame.
    df = get_dataframe()

    # If there are no expenses, return an empty dictionary.
    if df.empty:
        return {}

    # Create a temporary "day" column formatted as "YYYY-MM-DD" (e.g. "2026-09-25").
    df["day"] = df["date"].dt.strftime("%Y-%m-%d")

    # Group all rows by that day and calculate total expenditure per day.
    summary = df.groupby("day")["amount"].sum()

    # Return the dictionary of {day: total_amount}.
    return {
        day: round(float(amount), 2)
        for day, amount in summary.items()
    }
