import pandas as pd
import pytest
from data_loader import load_csv, get_column_summary

CSV_PATH = "data/sample.csv"


def test_load_csv_returns_dataframe():
    df = load_csv(CSV_PATH)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_load_csv_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        load_csv("nonexistent.csv")


def test_load_csv_parses_dates_when_column_named_date():
    df = load_csv(CSV_PATH)
    assert "date" in df.columns


def test_get_column_summary_returns_dict():
    df = load_csv(CSV_PATH)
    summary = get_column_summary(df)
    assert isinstance(summary, dict)
    assert "columns" in summary
    assert "shape" in summary
    assert "numeric_columns" in summary
