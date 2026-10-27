# ==============================================================================
# app/models.py - Pydantic Data Schemas & Validation
# ==============================================================================
# This file defines the data structures (schemas) for expenses.
# Pydantic validates incoming HTTP request data and formats outgoing responses.
# If a client sends invalid data (e.g., negative amount), Pydantic rejects it automatically.

# Import the standard Python 'date' type from datetime module to handle calendar dates.
from datetime import date

# Import core classes and functions from Pydantic:
# - BaseModel: The base class that all Pydantic schemas inherit from.
# - ConfigDict: Used to configure model behaviors and settings.
# - Field: Allows defining custom constraints (e.g. min/max length, value limits, defaults).
# - field_validator: A decorator used to define custom validation functions for specific fields.
from pydantic import BaseModel, ConfigDict, Field, field_validator


# Define 'ExpenseBase' as our foundational data model inheriting from Pydantic's 'BaseModel'.
# It contains fields common to creating, updating, and viewing an expense.
class ExpenseBase(BaseModel):
    # 'title' must be a string, minimum 1 character, maximum 100 characters long.
    title: str = Field(min_length=1, max_length=100)

    # 'amount' must be a floating-point number, strictly greater than 0 (gt=0),
    # and must not be infinity or NaN (not a number).
    amount: float = Field(gt=0, allow_inf_nan=False)

    # 'category' must be a string between 1 and 50 characters (e.g., 'Food', 'Bills').
    category: str = Field(min_length=1, max_length=50)

    # 'date' must be a valid calendar date, parsed from standard ISO string format (YYYY-MM-DD).
    date: date

    # 'notes' is an optional string field with default empty string "" and maximum length of 500 characters.
    notes: str = Field(default="", max_length=500)

    # @field_validator tells Pydantic to run this method on the 'title' and 'category' fields before saving.
    @field_validator("title", "category")
    # @classmethod means this method belongs to the class itself rather than a specific object instance.
    @classmethod
    # This validator removes accidental extra spaces around text and ensures it is not purely blank whitespace.
    def strip_required_text(cls, value: str) -> str:
        # .strip() removes leading and trailing whitespace from the string.
        value = value.strip()

        # If the string becomes empty after stripping, raise a ValueError with an error message.
        if not value:
            # Pydantic catches ValueError and turns it into an HTTP 422 Unprocessable Entity error for the user.
            raise ValueError("This field cannot be empty")

        # Return the cleaned string.
        return value

    # @field_validator tells Pydantic to run this method specifically on the 'notes' field.
    @field_validator("notes")
    # @classmethod binds this method to the class.
    @classmethod
    # This validator strips leading/trailing whitespace from the optional notes field.
    def strip_notes(cls, value: str) -> str:
        # Return the trimmed notes string (if empty string was given, it stays empty string).
        return value.strip()


# 'ExpenseCreate' inherits all fields from 'ExpenseBase'.
# When a client sends a POST request to add a new expense, they do NOT provide an 'id'
# (the server generates the ID), so we only require the base fields.
class ExpenseCreate(ExpenseBase):
    """Fields required to create an expense."""
    # 'pass' is a Python keyword that indicates an empty code block where no extra attributes are added.
    pass


# 'ExpenseUpdate' inherits all fields from 'ExpenseBase'.
# When updating an existing expense via a PUT request, all base fields are provided to overwrite the old data.
class ExpenseUpdate(ExpenseBase):
    """PUT replaces all editable expense fields."""
    # 'pass' means this class has the exact same structure as ExpenseBase without changes.
    pass


# 'ExpenseResponse' represents what our API returns back to clients.
# It includes all base fields (title, amount, category, date, notes) PLUS the unique 'id'.
class ExpenseResponse(ExpenseBase):
    """Expense representation returned by the API."""
    # 'id' is a required integer assigned by the database/CSV to identify this record.
    id: int

    # model_config allows customizing how Pydantic handles this model.
    # 'from_attributes=True' (formerly orm_mode) allows Pydantic to read data not just from dictionaries,
    # but also from Python objects (useful if integrating with ORMs or custom objects later).
    model_config = ConfigDict(from_attributes=True)
