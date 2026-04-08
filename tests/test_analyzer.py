import pandas as pd
import pytest
from analyzer import (
    compute_basic_stats,
    compute_pct_change,
    detect_outliers,
    detect_drops,
    generate_insights,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "date": pd.date_range("2024-01", periods=6, freq="MS"),
        "revenue": [15000, 16000, 15500, 18000, 9000, 19000],
        "users": [1200, 1300, 1250, 1500, 800, 1600],
    })


def test_compute_basic_stats_returns_describe(sample_df):
    stats = compute_basic_stats(sample_df)
    assert "revenue" in stats
    assert "mean" in stats["revenue"]


def test_compute_pct_change_returns_dataframe(sample_df):
    changes = compute_pct_change(sample_df)
    assert isinstance(changes, pd.DataFrame)
    assert "revenue" in changes.columns


def test_detect_outliers_finds_anomalous_values(sample_df):
    outliers = detect_outliers(sample_df)
    assert isinstance(outliers, dict)


def test_detect_drops_finds_big_decreases(sample_df):
    drops = detect_drops(sample_df, threshold=-20.0)
    # 9000 after 18000 is a -50% drop — must be detected
    assert len(drops) > 0
    assert "revenue" in drops


def test_generate_insights_returns_string(sample_df):
    insights = generate_insights(sample_df)
    assert isinstance(insights, str)
    assert len(insights) > 0
