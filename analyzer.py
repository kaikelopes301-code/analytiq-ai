import pandas as pd
import re


def get_snapshot(workbook: dict) -> dict:
    """Build a small summary used by the welcome screen."""
    sheets = workbook["sheets"]
    total_rows = sum(sheet["shape"][0] for sheet in sheets)
    total_formulas = sum(sheet["formula_count"] for sheet in sheets)
    total_empty_columns = sum(len(sheet["column_summary"]["empty_columns"]) for sheet in sheets)
    primary_sheet = _pick_primary_sheets(workbook, limit=1)[0] if sheets else None

    return {
        "sheet_count": workbook["sheet_count"],
        "total_rows": total_rows,
        "total_formulas": total_formulas,
        "total_empty_columns": total_empty_columns,
        "primary_sheet": primary_sheet["name"] if primary_sheet else None,
        "primary_rows": primary_sheet["shape"][0] if primary_sheet else 0,
        "filetype": workbook["filetype"],
    }


def generate_insights(workbook: dict) -> str:
    """Generate lightweight workbook-level insights for the prompt."""
    sheets = workbook["sheets"]
    snapshot = get_snapshot(workbook)
    story = _workbook_story(workbook)
    lines = [
        f"- Arquivo {workbook['filetype']} com {snapshot['sheet_count']} abas e {snapshot['total_rows']} linhas uteis.",
        f"- Foram detectadas {snapshot['total_formulas']} formulas e {snapshot['total_empty_columns']} colunas totalmente vazias.",
    ]
    if story:
        lines.append(f"- Leitura geral: {story}.")

    primary_sheets = _pick_primary_sheets(workbook, limit=3)
    if primary_sheets:
        lines.append(
            "- Abas com maior volume: "
            + ", ".join(f"{sheet['name']} ({sheet['shape'][0]} linhas)" for sheet in primary_sheets)
        )

    formula_sheets = [sheet for sheet in sheets if sheet["formula_count"] > 0]
    if formula_sheets:
        lines.append(
            "- Abas com formulas: "
            + ", ".join(f"{sheet['name']} ({sheet['formula_count']})" for sheet in formula_sheets[:4])
        )

    noisiest = _sheet_with_most_empty_columns(workbook)
    if noisiest and noisiest["column_summary"]["empty_columns"]:
        lines.append(
            f"- Aba com mais colunas vazias: {noisiest['name']} ({len(noisiest['column_summary']['empty_columns'])})."
        )

    primary_sheet = primary_sheets[0] if primary_sheets else None
    if primary_sheet:
        summary = primary_sheet["column_summary"]
        lines.append(
            f"- Aba principal {primary_sheet['name']} tem {len(summary['numeric_columns'])} colunas numericas, "
            f"{len(summary['date_columns'])} colunas de data e {len(summary['text_columns'])} colunas textuais."
        )
        lines.append(f"- Leitura provavel da aba principal: {_sheet_role(primary_sheet)}.")
        if summary["formula_columns"]:
            lines.append(f"- Colunas calculadas por formula na aba principal: {', '.join(summary['formula_columns'][:4])}.")
        high_missing = summary["mostly_empty_columns"][:3]
        if high_missing:
            lines.append(f"- Colunas quase vazias na aba principal: {', '.join(high_missing)}.")

    relationship_hints = _relationship_hints(workbook)
    if relationship_hints:
        lines.append("- Relacoes provaveis entre abas: " + "; ".join(relationship_hints[:3]))

    return "\n".join(lines)


def build_visual_snapshot(workbook: dict) -> dict:
    """Build a generic visual summary for the /insights command."""
    snapshot = get_snapshot(workbook)
    primary_sheet = _pick_primary_sheets(workbook, limit=1)[0] if workbook["sheets"] else None

    cards = [
        {"label": "Abas", "value": snapshot["sheet_count"], "caption": "estruturas detectadas"},
        {"label": "Linhas", "value": snapshot["total_rows"], "caption": "linhas uteis"},
        {"label": "Formulas", "value": snapshot["total_formulas"], "caption": "celulas com formula"},
        {"label": "Colunas vazias", "value": snapshot["total_empty_columns"], "caption": "campos sem dados"},
    ]

    sheets = []
    for sheet in _pick_primary_sheets(workbook, limit=min(6, len(workbook["sheets"]))):
        summary = sheet["column_summary"]
        sheets.append(
            {
                "name": sheet["name"],
                "rows": sheet["shape"][0],
                "columns": sheet["shape"][1],
                "numeric_columns": len(summary["numeric_columns"]),
                "date_columns": len(summary["date_columns"]),
                "formula_count": sheet["formula_count"],
                "key_columns": summary["usable_columns"][:4],
                "notes": _sheet_note(sheet),
            }
        )

    highlights = [
        f"Arquivo {workbook['filetype']} com {snapshot['sheet_count']} abas e {snapshot['total_rows']} linhas uteis.",
    ]
    if primary_sheet:
        highlights.append(
            f"Aba principal: {primary_sheet['name']} com {primary_sheet['shape'][0]} linhas e {primary_sheet['shape'][1]} colunas."
        )
    if snapshot["total_formulas"]:
        highlights.append(f"Foram detectadas {snapshot['total_formulas']} formulas no workbook.")
    else:
        highlights.append("Nenhuma formula foi detectada no workbook.")

    return {
        "cards": cards,
        "sheets": sheets,
        "highlights": highlights,
    }


def build_ai_context(workbook: dict) -> str:
    """Build a compact runtime context for spreadsheet QA."""
    sections = []
    snapshot = get_snapshot(workbook)
    sections.append(f"ARQUIVO: {workbook['filepath']}")
    sections.append(f"TIPO: {workbook['filetype']}")
    sections.append(
        f"WORKBOOK OVERVIEW: {snapshot['sheet_count']} abas, {snapshot['total_rows']} linhas uteis, "
        f"{snapshot['total_formulas']} formulas, {snapshot['total_empty_columns']} colunas vazias"
    )
    sections.append("")

    story = _workbook_story(workbook)
    if story:
        sections.append(f"LEITURA EXECUTIVA: {story}")
        sections.append("")

    sections.append("LEITURA HUMANA DO ARQUIVO:")
    for sheet in _ordered_sheets(workbook)[:8]:
        sections.append(f"- {sheet['name']}: {_sheet_role(sheet)}")
    relationship_hints = _relationship_hints(workbook)
    if relationship_hints:
        for hint in relationship_hints[:4]:
            sections.append(f"- Relacao sugerida: {hint}")
    sections.append("")

    for sheet in _ordered_sheets(workbook):
        summary = sheet["column_summary"]
        sections.append(f"ABA: {sheet['name']}")
        sections.append(f"- leitura provavel: {_sheet_role(sheet)}")
        sections.append(
            f"- shape: {sheet['shape'][0]} linhas x {sheet['shape'][1]} colunas "
            f"(removidas {sheet['empty_rows_removed']} linhas totalmente vazias)"
        )
        sections.append(f"- colunas principais: {', '.join(summary['usable_columns'][:10])}")
        sections.append(
            f"- tipos: {len(summary['numeric_columns'])} numericas, "
            f"{len(summary['date_columns'])} datas, {len(summary['text_columns'])} textuais"
        )
        if summary["likely_id_columns"]:
            sections.append(f"- possiveis IDs: {', '.join(summary['likely_id_columns'])}")
        if summary["formula_columns"]:
            sections.append(f"- colunas calculadas por formula: {', '.join(summary['formula_columns'][:6])}")
        if summary["formula_only_columns"]:
            sections.append(f"- colunas sem valor cacheado, mas com formula: {', '.join(summary['formula_only_columns'][:6])}")
        if summary["empty_columns"]:
            sections.append(f"- colunas realmente vazias: {', '.join(summary['empty_columns'][:6])}")
        if summary["mostly_empty_columns"]:
            sections.append(f"- colunas quase vazias: {', '.join(summary['mostly_empty_columns'][:6])}")

        stats_lines = _numeric_stats_lines(sheet["dataframe"], summary["numeric_columns"])
        if stats_lines:
            sections.append("- estatisticas numericas:")
            sections.extend(stats_lines)

        category_lines = _top_category_lines(sheet["dataframe"], summary["text_columns"])
        if category_lines:
            sections.append("- categorias e padroes textuais:")
            sections.extend(category_lines)

        if sheet["formula_examples"]:
            sections.append("- exemplos de formulas:")
            functions = _formula_function_names(sheet["formula_examples"])
            if functions:
                sections.append(f"  funcoes usadas: {', '.join(functions[:6])}")
            for item in sheet["formula_examples"][:3]:
                sections.append(f"  {item['cell']}: {item['formula'][:220]}")

        preview_lines = _preview_lines(sheet["preview"])
        if preview_lines:
            sections.append("- amostra de linhas:")
            sections.extend(preview_lines[:1])

        sections.append("")

    return "\n".join(sections).strip()


def _pick_primary_sheets(workbook: dict, limit: int = 3) -> list[dict]:
    """Sort sheets by volume and return the most relevant ones."""
    sheets = list(workbook["sheets"])
    sheets.sort(
        key=lambda sheet: (
            sheet["shape"][0],
            len(sheet["column_summary"]["usable_columns"]),
            sheet["formula_count"],
        ),
        reverse=True,
    )
    return sheets[:limit]


def _ordered_sheets(workbook: dict) -> list[dict]:
    """Order sheets by semantic importance first, then by size."""
    sheets = list(workbook["sheets"])
    sheets.sort(
        key=lambda sheet: (
            _sheet_priority(sheet),
            -sheet["shape"][0],
            -sheet["formula_count"],
        )
    )
    return sheets


def _sheet_with_most_empty_columns(workbook: dict) -> dict | None:
    """Return the sheet with the highest number of empty columns."""
    sheets = workbook["sheets"]
    if not sheets:
        return None
    return max(sheets, key=lambda sheet: len(sheet["column_summary"]["empty_columns"]))


def _numeric_stats_lines(dataframe: pd.DataFrame, numeric_columns: list[str]) -> list[str]:
    """Build a few summary lines for numeric columns."""
    lines = []
    for column in numeric_columns[:4]:
        series = dataframe[column].dropna()
        if series.empty:
            continue
        lines.append(
            f"  {column}: min={series.min():.2f}, max={series.max():.2f}, "
            f"mean={series.mean():.2f}"
        )
    return lines


def _preview_lines(preview: list[dict]) -> list[str]:
    """Render preview rows as compact key=value lines."""
    lines = []
    for row in preview[:2]:
        parts = [f"{key}={value}" for key, value in row.items() if str(value) != ""]
        if parts:
            lines.append("  " + " | ".join(parts))
    return lines


def _sheet_note(sheet: dict) -> str:
    """Return a compact note for the overview table."""
    summary = sheet["column_summary"]
    notes = []
    if summary["likely_id_columns"]:
        notes.append(f"id: {summary['likely_id_columns'][0]}")
    if summary["date_columns"]:
        notes.append(f"datas: {summary['date_columns'][0]}")
    if summary["formula_columns"]:
        notes.append(f"formulas: {summary['formula_columns'][0]}")
    if not notes:
        notes.append(f"{len(summary['text_columns'])} colunas textuais")
    return " | ".join(notes)


def _sheet_role(sheet: dict) -> str:
    """Infer a likely business role for the sheet."""
    normalized_name = _normalize_text(sheet["name"])
    summary = sheet["column_summary"]
    rows, columns = sheet["shape"]

    if "readme" in normalized_name or "glossario" in normalized_name:
        return "explica o contexto do arquivo e serve como guia de leitura"
    if "resumo" in normalized_name or "executivo" in normalized_name or "overview" in normalized_name:
        return "consolida os principais indicadores do negocio em formato executivo"
    if "financeiro" in normalized_name or "dre" in normalized_name:
        return "resume a performance financeira mensal e a estrutura de custos"
    if "forecast" in normalized_name or "meta" in normalized_name:
        return "compara metas, forecast e realizado"
    if "cliente" in normalized_name:
        return "cadastro mestre da carteira de clientes"
    if "contrato" in normalized_name or "assinatura" in normalized_name:
        return "mostra a carteira contratual, MRR e configuracao comercial"
    if "fatura" in normalized_name or "pagamento" in normalized_name:
        return "mostra faturamento, cobranca e recebimento"
    if "pipeline" in normalized_name or "venda" in normalized_name:
        return "mostra o funil comercial e as oportunidades abertas ou ganhas"
    if "uso" in normalized_name or "produto" in normalized_name:
        return "mostra adocao e intensidade de uso do produto"
    if "plano" in normalized_name:
        return "catalogo de planos, modulos e regras comerciais"
    if "suporte" in normalized_name or "ticket" in normalized_name:
        return "mostra a operacao de suporte e qualidade de atendimento"
    if "health" in normalized_name or "cs" in normalized_name:
        return "mostra saude da base, risco de churn e renovacao"

    if rows <= 12 and sheet["formula_count"] > 0 and len(summary["numeric_columns"]) >= 2:
        return "parece uma aba de resumo ou consolidacao com calculos"
    if summary["likely_id_columns"] and len(summary["text_columns"]) >= 2 and len(summary["numeric_columns"]) <= 2:
        return "parece uma base cadastral ou dimensao de entidades"
    if summary["date_columns"] and len(summary["numeric_columns"]) >= 2 and rows >= 12:
        return "parece uma base historica ou transacional com recorte temporal"
    if sheet["formula_count"] > 0 and rows >= 20:
        return "parece uma aba operacional com colunas calculadas"
    if rows <= 20 and columns <= 6:
        return "parece uma aba curta de apoio, parametros ou lookup"
    return "parece uma aba operacional com dados brutos"


def _sheet_priority(sheet: dict) -> int:
    """Return a stable semantic priority for context ordering."""
    normalized_name = _normalize_text(sheet["name"])
    if "resumo" in normalized_name or "executivo" in normalized_name:
        return 0
    if "readme" in normalized_name:
        return 1
    if "financeiro" in normalized_name or "dre" in normalized_name:
        return 2
    if "forecast" in normalized_name or "meta" in normalized_name:
        return 3
    if "contrato" in normalized_name or "assinatura" in normalized_name:
        return 4
    if "fatura" in normalized_name or "pagamento" in normalized_name:
        return 5
    if "cliente" in normalized_name:
        return 6
    if "pipeline" in normalized_name or "venda" in normalized_name:
        return 7
    if "uso" in normalized_name:
        return 8
    if "suporte" in normalized_name or "ticket" in normalized_name:
        return 9
    if "health" in normalized_name or normalized_name == "cs_health":
        return 10
    if "plano" in normalized_name or "produto" in normalized_name:
        return 11
    return 20


def _top_category_lines(dataframe: pd.DataFrame, text_columns: list[str]) -> list[str]:
    """Return top category hints for low-cardinality text columns."""
    lines = []
    for column in text_columns[:4]:
        series = dataframe[column].dropna().astype(str).str.strip()
        if series.empty:
            continue
        unique_count = series.nunique()
        if unique_count > 10:
            continue
        top_values = series.value_counts().head(3)
        formatted = ", ".join(f"{value} ({count})" for value, count in top_values.items())
        lines.append(f"  {column}: {formatted}")
    return lines


def _relationship_hints(workbook: dict) -> list[str]:
    """Infer simple relationships from shared column names across sheets."""
    hints = []
    sheets = workbook["sheets"]
    for index, left in enumerate(sheets):
        left_columns = set(left["column_summary"]["usable_columns"])
        for right in sheets[index + 1:]:
            shared = left_columns & set(right["column_summary"]["usable_columns"])
            join_keys = [column for column in shared if column.lower().endswith("_id") or column.lower() in {"id", "date", "month"}]
            if join_keys:
                hints.append(f"{left['name']} e {right['name']} podem se conectar por {', '.join(sorted(join_keys)[:3])}")
            elif len(shared) >= 3:
                hints.append(f"{left['name']} e {right['name']} compartilham colunas como {', '.join(sorted(shared)[:3])}")
    return hints


def _formula_function_names(formula_examples: list[dict]) -> list[str]:
    """Extract the main spreadsheet functions used in formula examples."""
    names = []
    for item in formula_examples:
        formula = item.get("formula", "")
        matches = re.findall(r"([A-Z][A-Z0-9\.]+)\(", formula)
        names.extend(matches)
    return list(dict.fromkeys(names))


def _workbook_story(workbook: dict) -> str | None:
    """Infer a human-friendly reading of the workbook theme."""
    sheet_names = {_normalize_text(sheet["name"]) for sheet in workbook["sheets"]}
    if {"clientes", "contratos_assinaturas", "faturas_pagamentos", "uso_produto", "cs_health"} <= sheet_names:
        return "o arquivo parece representar a operacao completa de uma empresa SaaS B2B, cobrindo vendas, contratos, faturamento, uso, suporte e saude da base"

    readme_sheet = next((sheet for sheet in workbook["sheets"] if "readme" in _normalize_text(sheet["name"])), None)
    if readme_sheet and readme_sheet["preview"]:
        description = readme_sheet["preview"][0].get("descricao")
        if description:
            return str(description)
    return None


def _normalize_text(value: str) -> str:
    """Normalize sheet names for semantic matching."""
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )
