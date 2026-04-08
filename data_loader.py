import pandas as pd
from pathlib import Path


def load_csv(filepath: str) -> pd.DataFrame:
    """Load a CSV file and return a cleaned DataFrame."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    df = pd.read_csv(path)
    df = _try_parse_date_column(df)
    return df


def _try_parse_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Attempt to parse a column named 'date' as datetime."""
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"])
        except Exception:
            pass
    return df


def get_column_summary(df: pd.DataFrame) -> dict:
    """Return metadata about the DataFrame columns."""
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    return {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "numeric_columns": numeric_cols,
        "dtypes": df.dtypes.astype(str).to_dict(),
    }
