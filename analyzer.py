import pandas as pd

_KEY_METRICS = [
    "mrr",
    "churn_rate",
    "nps",
    "gross_margin_pct",
    "cac",
    "ltv",
    "ltv_cac_ratio",
    "active_customers",
]

_TEXT_CONTEXT_COLUMNS = [
    "focus_segment",
    "primary_channel",
    "product_launch",
    "top_new_logos",
    "top_expansion_accounts",
    "churned_accounts",
    "customer_story",
    "risk_signal",
]

_TABLE_CONTEXT_COLUMNS = [
    "date",
    "mrr",
    "active_customers",
    "new_customers",
    "churned_customers",
    "churn_rate",
    "nps",
    "cac",
    "ltv_cac_ratio",
    "net_revenue_retention_pct",
    "top_new_logos",
    "top_expansion_accounts",
    "risk_signal",
]


def compute_basic_stats(df: pd.DataFrame) -> dict:
    """Return descriptive statistics for all numeric columns."""
    numeric_df = df.select_dtypes(include="number")
    stats = {}
    for col in numeric_df.columns:
        desc = numeric_df[col].describe()
        stats[col] = desc.to_dict()
    return stats


def compute_pct_change(df: pd.DataFrame) -> pd.DataFrame:
    """Return period-over-period percentage change for numeric columns."""
    numeric_df = df.select_dtypes(include="number")
    return numeric_df.pct_change() * 100


def detect_outliers(df: pd.DataFrame) -> dict:
    """Detect outliers using IQR method. Returns {col: [outlier_values]}."""
    numeric_df = df.select_dtypes(include="number")
    outliers = {}
    for col in numeric_df.columns:
        q1 = numeric_df[col].quantile(0.25)
        q3 = numeric_df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        flagged = numeric_df[col][(numeric_df[col] < lower) | (numeric_df[col] > upper)]
        if not flagged.empty:
            outliers[col] = flagged.tolist()
    return outliers


def detect_drops(df: pd.DataFrame, threshold: float = -15.0) -> dict:
    """Find columns with period drops below the threshold (negative %)."""
    changes = compute_pct_change(df)
    drops = {}
    for col in changes.columns:
        significant = changes[col][changes[col] < threshold].dropna()
        if not significant.empty:
            drops[col] = [
                {"index": int(i), "pct_change": round(v, 2)}
                for i, v in significant.items()
            ]
    return drops


def _pct_change(new, old):
    """Safely compute percentage change."""
    return (new - old) / abs(old) * 100 if old != 0 else None


def _available_columns(df: pd.DataFrame, candidates: list[str]) -> list[str]:
    """Return columns from candidates that exist in the DataFrame."""
    return [col for col in candidates if col in df.columns]


def _format_period(value) -> str:
    """Format a date-like value as YYYY-MM when possible."""
    return str(value)[:7]


def _text_value(row: pd.Series, column: str) -> str | None:
    """Return a clean text value if present."""
    if column not in row.index:
        return None
    value = row[column]
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text if text else None


def generate_insights(df: pd.DataFrame) -> str:
    """Generate a concise summary focused on key business metrics."""
    lines = []
    stats = compute_basic_stats(df)
    drops = detect_drops(df)
    outliers = detect_outliers(df)
    date_col = df["date"] if "date" in df.columns else None
    key_cols = [c for c in _KEY_METRICS if c in stats]

    for col in key_cols[:5]:
        s = stats[col]
        lines.append(f"- {col}: mean={s['mean']:.2f}, min={s['min']:.2f}, max={s['max']:.2f}")

    top_drops = []
    for col, drop_list in drops.items():
        if col not in key_cols:
            continue
        for d in drop_list:
            idx = d["index"]
            label = _format_period(date_col.iloc[idx]) if date_col is not None else f"periodo {idx}"
            top_drops.append((abs(d["pct_change"]), col, label, d["pct_change"]))

    top_drops.sort(reverse=True)
    if top_drops:
        for _, col, label, pct in top_drops[:5]:
            lines.append(f"- QUEDA em '{col}' em {label}: {pct:.1f}%")
    else:
        lines.append("- Sem quedas significativas nos indicadores-chave.")

    key_outliers = {k: v for k, v in outliers.items() if k in key_cols}
    for col, vals in list(key_outliers.items())[:2]:
        lines.append(f"- OUTLIER em '{col}': {[round(v, 2) for v in vals[:3]]}")

    if not df.empty:
        last = df.iloc[-1]
        logos = _text_value(last, "top_new_logos")
        expansions = _text_value(last, "top_expansion_accounts")
        risk = _text_value(last, "risk_signal")
        if logos:
            lines.append(f"- Logos em destaque no ultimo mes: {logos}")
        if expansions:
            lines.append(f"- Expansoes relevantes no ultimo mes: {expansions}")
        if risk:
            lines.append(f"- Risco operacional atual: {risk}")

    return "\n".join(lines)


def get_snapshot(df: pd.DataFrame) -> dict:
    """Return last-period values and MoM changes for the dashboard display."""
    last = df.iloc[-1]
    prev = df.iloc[-2]
    has_date = "date" in df.columns
    period = _format_period(last["date"]) if has_date else f"periodo {len(df) - 1}"

    return {
        "period": period,
        "months": len(df),
        "mrr": last["mrr"],
        "mrr_chg": _pct_change(last["mrr"], prev["mrr"]),
        "customers": int(last["active_customers"]),
        "customers_chg": _pct_change(last["active_customers"], prev["active_customers"]),
        "churn_rate": last["churn_rate"] * 100,
        "churn_chg": (last["churn_rate"] - prev["churn_rate"]) * 100,
        "nps": int(last["nps"]),
        "nps_chg": float(last["nps"] - prev["nps"]),
        "cac": last["cac"],
        "cac_chg": _pct_change(last["cac"], prev["cac"]),
        "ltv": last["ltv"],
        "ltv_chg": _pct_change(last["ltv"], prev["ltv"]),
        "ltv_cac": last["ltv_cac_ratio"],
        "ltv_cac_chg": float(last["ltv_cac_ratio"] - prev["ltv_cac_ratio"]),
        "gross_margin": last["gross_margin_pct"],
        "gross_margin_chg": float(last["gross_margin_pct"] - prev["gross_margin_pct"]),
    }


def build_visual_snapshot(df: pd.DataFrame) -> dict:
    """Create structured data for the on-demand visual insights board."""
    snapshot = get_snapshot(df)
    has_date = "date" in df.columns
    dates = df["date"].astype(str) if has_date else pd.Series(dtype="object")
    last = df.iloc[-1]
    prev = df.iloc[-2]

    period = snapshot["period"]
    prev_period = _format_period(prev["date"]) if has_date else f"periodo {len(df) - 2}"
    year_ago = df.iloc[-13] if len(df) >= 13 else None
    year_ago_period = _format_period(year_ago["date"]) if (has_date and year_ago is not None) else None

    cards = [
        {
            "label": "MRR",
            "value": snapshot["mrr"],
            "change": snapshot["mrr_chg"],
            "format": "currency",
            "good_up": True,
            "caption": f"fechamento de {period}",
        },
        {
            "label": "Clientes",
            "value": snapshot["customers"],
            "change": snapshot["customers_chg"],
            "format": "integer",
            "good_up": True,
            "caption": "base ativa",
        },
        {
            "label": "Churn",
            "value": snapshot["churn_rate"],
            "change": snapshot["churn_chg"],
            "format": "percent",
            "good_up": False,
            "change_unit": "pp",
            "change_decimals": 2,
            "caption": "saude da retencao",
        },
        {
            "label": "NPS",
            "value": snapshot["nps"],
            "change": snapshot["nps_chg"],
            "format": "integer",
            "good_up": True,
            "change_unit": " pts",
            "change_decimals": 0,
            "caption": "voz do cliente",
        },
        {
            "label": "CAC",
            "value": snapshot["cac"],
            "change": snapshot["cac_chg"],
            "format": "currency",
            "good_up": False,
            "caption": "custo de aquisicao",
        },
        {
            "label": "LTV / CAC",
            "value": snapshot["ltv_cac"],
            "change": snapshot["ltv_cac_chg"],
            "format": "ratio",
            "good_up": True,
            "change_unit": "x",
            "caption": "eficiencia unitaria",
        },
    ]

    recent_window = min(6, len(df))
    recent = df.tail(recent_window).reset_index(drop=True)
    labels = (
        dates.iloc[-recent_window:].str[:7].tolist()
        if has_date
        else [str(i) for i in range(len(df) - recent_window, len(df))]
    )
    trends = [
        {
            "label": "MRR",
            "series": recent["mrr"].tolist(),
            "labels": labels,
            "format": "currency",
            "current": snapshot["mrr"],
            "change": snapshot["mrr_chg"],
            "good_up": True,
        },
        {
            "label": "Clientes",
            "series": recent["active_customers"].tolist(),
            "labels": labels,
            "format": "integer",
            "current": snapshot["customers"],
            "change": snapshot["customers_chg"],
            "good_up": True,
        },
        {
            "label": "NPS",
            "series": recent["nps"].tolist(),
            "labels": labels,
            "format": "integer",
            "current": snapshot["nps"],
            "change": snapshot["nps_chg"],
            "good_up": True,
            "change_unit": " pts",
            "change_decimals": 0,
        },
        {
            "label": "Churn",
            "series": (recent["churn_rate"] * 100).tolist(),
            "labels": labels,
            "format": "percent",
            "current": snapshot["churn_rate"],
            "change": snapshot["churn_chg"],
            "good_up": False,
            "change_unit": "pp",
            "change_decimals": 2,
        },
    ]

    highlights = [
        {
            "title": "Receita",
            "tone": "positive" if (snapshot["mrr_chg"] or 0) >= 0 else "warning",
            "body": (
                f"{period} fechou com MRR de {last['mrr']:,.0f}, "
                f"{_pct_change(last['mrr'], prev['mrr']):+.1f}% contra {prev_period}."
            ),
        },
        {
            "title": "Retencao",
            "tone": "positive" if snapshot["churn_chg"] <= 0 else "warning",
            "body": (
                f"Churn em {snapshot['churn_rate']:.2f}% e NPS em {snapshot['nps']}, "
                f"mostrando {'estabilidade' if snapshot['churn_chg'] <= 0 else 'pressao'} na experiencia."
            ),
        },
        {
            "title": "Eficiencia",
            "tone": "positive" if (snapshot["cac_chg"] or 0) <= 0 and snapshot["ltv_cac"] >= 3 else "warning",
            "body": (
                f"CAC em {last['cac']:,.0f} e LTV/CAC em {last['ltv_cac_ratio']:.2f}x "
                f"no fechamento mais recente."
            ),
        },
    ]

    logos = _text_value(last, "top_new_logos")
    if logos:
        highlights.append(
            {
                "title": "Contas novas",
                "tone": "positive",
                "body": f"Novos logos de destaque em {period}: {logos}.",
            }
        )

    if year_ago is not None:
        highlights.append(
            {
                "title": "Janela anual",
                "tone": "positive",
                "body": (
                    f"Contra {year_ago_period}, o MRR variou "
                    f"{_pct_change(last['mrr'], year_ago['mrr']):+.1f}% e a base ativa "
                    f"{_pct_change(last['active_customers'], year_ago['active_customers']):+.1f}%."
                ),
            }
        )

    return {
        "period": period,
        "previous_period": prev_period,
        "months": len(df),
        "cards": cards,
        "trends": trends,
        "highlights": highlights,
    }


def build_ai_context(df: pd.DataFrame) -> str:
    """Build a rich, structured context that helps the model answer accurately."""
    sections = []
    has_date = "date" in df.columns
    dates = df["date"].astype(str) if has_date else None

    last_month = dates.iloc[-1][:7] if has_date else f"periodo {len(df)-1}"
    prev_month = dates.iloc[-2][:7] if has_date else f"periodo {len(df)-2}"
    year_ago_month = dates.iloc[-13][:7] if (has_date and len(df) >= 13) else None
    first_month = dates.iloc[0][:7] if has_date else "periodo 0"

    sections.append(f"PERIODO DOS DADOS: {first_month} ate {last_month} ({len(df)} meses)")
    sections.append(f"ULTIMO MES NOS DADOS: {last_month}")
    sections.append(f"MES ANTERIOR AO ULTIMO: {prev_month}")
    if year_ago_month:
        sections.append(f"MESMO MES DO ANO PASSADO: {year_ago_month}")
    sections.append("")

    key_cols = [c for c in _KEY_METRICS if c in df.columns]
    last = df.iloc[-1]
    prev = df.iloc[-2]

    sections.append(f"ULTIMO MES vs MES ANTERIOR ({last_month} vs {prev_month}):")
    for col in key_cols:
        lv, pv = last[col], prev[col]
        if pv != 0:
            pct = (lv - pv) / abs(pv) * 100
            direction = "alta" if pct > 0.5 else ("queda" if pct < -0.5 else "estavel")
            sections.append(f"  {col}: {lv:.2f} vs {pv:.2f} ({pct:+.1f}%) {direction}")
        else:
            sections.append(f"  {col}: {lv:.2f}")
    sections.append("")

    compare_cols = _available_columns(
        df,
        [
            "net_revenue_retention_pct",
            "gross_revenue_retention_pct",
            "expansion_mrr",
            "contraction_mrr",
            "reactivation_mrr",
            "pipeline_coverage",
            "win_rate_pct",
            "support_sla_pct",
            "onboarding_days",
        ],
    )
    if compare_cols:
        sections.append("INDICADORES OPERACIONAIS DO ULTIMO MES:")
        for col in compare_cols:
            sections.append(f"  {col}: {last[col]}")
        sections.append("")

    if year_ago_month and len(df) >= 13:
        year_ago = df.iloc[-13]
        sections.append(f"ULTIMO MES vs MESMO MES ANO PASSADO ({last_month} vs {year_ago_month}):")
        for col in key_cols:
            lv, yv = last[col], year_ago[col]
            if yv != 0:
                pct = (lv - yv) / abs(yv) * 100
                intensity = "forte alta" if pct > 20 else ("alta" if pct > 0.5 else ("forte queda" if pct < -20 else ("queda" if pct < -0.5 else "estavel")))
                sections.append(f"  {col}: {lv:.2f} vs {yv:.2f} ({pct:+.1f}%) {intensity}")
        sections.append("")

    if len(df) >= 6:
        last6 = df.tail(6)
        labels = dates.iloc[-6:].str[:7].tolist() if has_date else [str(i) for i in range(len(df) - 6, len(df))]
        sections.append("TENDENCIA ULTIMOS 6 MESES:")
        for col in key_cols[:4]:
            vals = " -> ".join(f"{d}={last6.iloc[i][col]:.0f}" for i, d in enumerate(labels))
            sections.append(f"  {col}: {vals}")
        sections.append("")

    text_cols = _available_columns(df, _TEXT_CONTEXT_COLUMNS)
    if text_cols:
        sections.append("CONTEXTO QUALITATIVO DO ULTIMO MES:")
        for col in text_cols:
            value = _text_value(last, col)
            if value:
                sections.append(f"  {col}: {value}")
        sections.append("")

        sections.append("CONTEXTO QUALITATIVO ULTIMOS 4 MESES:")
        for _, row in df.tail(4).iterrows():
            label = _format_period(row["date"]) if has_date else "periodo"
            pieces = []
            for col in text_cols:
                value = _text_value(row, col)
                if value:
                    pieces.append(f"{col}={value}")
            if pieces:
                sections.append(f"  {label}: " + " | ".join(pieces))
        sections.append("")

    drops = detect_drops(df, threshold=-8.0)
    mrr_drops = drops.get("mrr", [])
    if mrr_drops:
        worst = max(mrr_drops, key=lambda x: abs(x["pct_change"]))
        idx = worst["index"]
        label = _format_period(df["date"].iloc[idx]) if has_date else f"periodo {idx}"
        sections.append(f"PIOR QUEDA DE MRR: {label} ({worst['pct_change']:.1f}%)")

    outliers = detect_outliers(df)
    key_outliers = {k: v for k, v in outliers.items() if k in key_cols}
    for col, vals in list(key_outliers.items())[:2]:
        sections.append(f"OUTLIER em {col}: {[round(v, 2) for v in vals[:3]]}")

    if mrr_drops or key_outliers:
        sections.append("")

    stats = compute_basic_stats(df)
    sections.append("ESTATISTICAS HISTORICAS:")
    for col in key_cols:
        s = stats[col]
        sections.append(f"  {col}: media={s['mean']:.2f}, min={s['min']:.2f}, max={s['max']:.2f}")
    sections.append("")

    table_cols = _available_columns(df, _TABLE_CONTEXT_COLUMNS)
    if table_cols:
        sections.append("TABELA RESUMIDA ULTIMOS 12 MESES:")
        sections.append(df[table_cols].tail(12).to_string(index=False))
    else:
        sections.append("TABELA RESUMIDA ULTIMOS 12 MESES:")
        sections.append(df.tail(12).to_string(index=False))

    return "\n".join(sections)
