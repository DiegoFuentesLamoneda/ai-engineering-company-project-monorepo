"""
Safe snippet for basic pandas cleaning. Copy and adapt for your dataset.
Run: python pandas_clean.py  (ensure pandas is installed)
Errors go to stderr and exit with code 1, so a pipeline that runs it stops.
"""
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is not installed (pip install pandas).", file=sys.stderr)
    sys.exit(1)

# Adjust to your dataset: the file and the columns the cleaning needs.
DATA_PATH = Path("data.csv")
REQUIRED_COLUMNS: list[str] = []  # e.g. ["ticket_id", "status"]

if not DATA_PATH.is_file():
    print(f"Error: '{DATA_PATH}' does not exist.", file=sys.stderr)
    sys.exit(1)

# Load (adjust kwargs as needed)
try:
    df = pd.read_csv(DATA_PATH)  # or read_json, read_excel
except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
    print(f"Error: '{DATA_PATH}' is not a readable CSV: {error}", file=sys.stderr)
    sys.exit(1)
except OSError as error:
    # No permission, or locked by another program.
    print(f"Error: could not open '{DATA_PATH}': {error.strerror}", file=sys.stderr)
    sys.exit(1)

missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
if missing:
    print(f"Error: missing required columns: {', '.join(missing)}", file=sys.stderr)
    sys.exit(1)

print("df_shape", df.shape)
print("df_dtypes", df.dtypes)

# Drop fully null columns
df = df.dropna(axis=1, how="all")
print("df_shape_after_drop_all_null_cols", df.shape)

# Fill or drop nulls in key columns (customise columns)
# df = df.dropna(subset=["required_col"])
# df["optional_col"] = df["optional_col"].fillna(0)

# Normalise column names (optional)
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
print("df_columns", list(df.columns))

# Deduplicate (optional)
before = len(df)
df = df.drop_duplicates()
print("rows_dropped_duplicates", before - len(df))

# Sample output
print("df_head", df.head())
