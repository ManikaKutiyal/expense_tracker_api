from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

CSV_FILE = DATA_DIR / "expenses.csv"

CSV_COLUMNS = [
    "id",
    "title",
    "amount",
    "category",
    "date",
    "notes"
]
