import pandas as pd


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


def generate_insights(df: pd.DataFrame) -> str:
    """Generate a human-readable summary of the most relevant findings."""
    lines = []
    stats = compute_basic_stats(df)
    drops = detect_drops(df)
    outliers = detect_outliers(df)

    for col, s in stats.items():
        lines.append(
            f"- {col}: mean={s['mean']:.2f}, min={s['min']:.2f}, max={s['max']:.2f}"
        )

    if drops:
        for col, drop_list in drops.items():
            for d in drop_list:
                lines.append(
                    f"- QUEDA em '{col}' no período {d['index']}: {d['pct_change']}%"
                )
    else:
        lines.append("- Nenhuma queda significativa detectada.")

    if outliers:
        for col, vals in outliers.items():
            lines.append(f"- OUTLIER em '{col}': valores {vals}")
    else:
        lines.append("- Nenhum outlier detectado.")

    return "\n".join(lines)
