import pandas as pd
import pytest

from analyzer import (
    build_ai_context,
    build_visual_snapshot,
    compute_basic_stats,
    compute_pct_change,
    detect_drops,
    detect_outliers,
    generate_insights,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "date": pd.date_range("2024-01", periods=6, freq="MS"),
        "revenue": [15000, 16000, 15500, 18000, 9000, 19000],
        "users": [1200, 1300, 1250, 1500, 800, 1600],
    })


@pytest.fixture
def saas_df():
    return pd.DataFrame({
        "date": pd.date_range("2024-01", periods=6, freq="MS"),
        "mrr": [100000, 104000, 109000, 115000, 121000, 128000],
        "churn_rate": [0.025, 0.023, 0.022, 0.021, 0.019, 0.018],
        "nps": [42, 45, 47, 49, 53, 56],
        "gross_margin_pct": [71.2, 72.1, 72.8, 73.4, 74.2, 75.1],
        "cac": [620, 610, 598, 580, 562, 548],
        "ltv": [2100, 2250, 2400, 2580, 2750, 2940],
        "ltv_cac_ratio": [3.39, 3.69, 4.01, 4.45, 4.89, 5.36],
        "active_customers": [2100, 2180, 2270, 2385, 2490, 2620],
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
    assert len(drops) > 0
    assert "revenue" in drops


def test_generate_insights_returns_string(sample_df):
    insights = generate_insights(sample_df)
    assert isinstance(insights, str)
    assert len(insights) > 0


def test_build_visual_snapshot_returns_visual_sections(saas_df):
    visual = build_visual_snapshot(saas_df)
    assert visual["period"] == "2024-06"
    assert len(visual["cards"]) == 6
    assert len(visual["trends"]) == 4
    assert len(visual["highlights"]) >= 3


def test_build_ai_context_includes_qualitative_customer_context(saas_df):
    enriched = saas_df.copy()
    enriched["focus_segment"] = [
        "PMEs",
        "PMEs",
        "mid-market",
        "mid-market",
        "enterprise",
        "enterprise",
    ]
    enriched["top_new_logos"] = [
        "Casa Norte",
        "AtlasPay",
        "Hospital Santa Aurora",
        "VerdeLog",
        "Nexa Saude",
        "Grupo Prisma Varejo",
    ]
    enriched["risk_signal"] = [
        "onboarding manual",
        "pipeline curto",
        "pressao no suporte",
        "renovacoes longas",
        "expansao concentrada",
        "implantacoes enterprise",
    ]

    context = build_ai_context(enriched)

    assert "CONTEXTO QUALITATIVO DO ULTIMO MES" in context
    assert "Grupo Prisma Varejo" in context
    assert "implantacoes enterprise" in context
