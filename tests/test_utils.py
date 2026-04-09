from rich.console import Console
from rich.panel import Panel

from utils import (
    make_reasoning_panel,
    print_header,
    print_visual_insights,
    print_welcome,
    render_assistant_message,
    truncate_text,
    wants_visual_summary,
)


def _visual_snapshot():
    return {
        "cards": [
            {"label": "Abas", "value": 4, "caption": "estruturas detectadas"},
            {"label": "Linhas", "value": 1220, "caption": "linhas uteis"},
            {"label": "Formulas", "value": 18, "caption": "celulas com formula"},
            {"label": "Colunas vazias", "value": 3, "caption": "campos sem dados"},
        ],
        "sheets": [
            {
                "name": "Revenue",
                "rows": 320,
                "columns": 12,
                "numeric_columns": 6,
                "date_columns": 1,
                "formula_count": 8,
                "notes": "id: invoice_id | datas: month",
            },
            {
                "name": "Customers",
                "rows": 180,
                "columns": 9,
                "numeric_columns": 2,
                "date_columns": 1,
                "formula_count": 0,
                "notes": "id: customer_id",
            },
        ],
        "highlights": [
            "Arquivo xlsx com 4 abas e 1220 linhas uteis.",
            "Aba principal: Revenue com 320 linhas e 12 colunas.",
            "Foram detectadas 18 formulas no workbook.",
        ],
    }


def test_make_reasoning_panel_returns_panel():
    text = "- Aba Revenue com formulas"
    panel = make_reasoning_panel(text)
    assert isinstance(panel, Panel)
    assert panel.renderable == text
    assert panel.title == "Raciocinio"
    assert panel.border_style == "dim"
    assert panel.padding == (0, 1)


def test_truncate_text_limits_length():
    long_text = "a" * 1000
    result = truncate_text(long_text, max_chars=100)
    assert len(result) <= 103


def test_print_header_runs_without_error():
    console = Console(record=True)
    print_header(console, "gemini-2.5-flash", "data/sample.csv")
    output = console.export_text()
    assert "gemini-2.5-flash" in output
    assert "data/sample.csv" in output


def test_print_welcome_runs_without_error():
    console = Console(record=True, width=120)
    snapshot = {
        "sheet_count": 4,
        "total_rows": 1220,
        "total_formulas": 18,
        "primary_sheet": "Revenue",
    }
    print_welcome(console, "data/sample.xlsx", "gemini-2.5-flash", snapshot)
    output = console.export_text()
    assert "Bem-vindo de volta" in output
    assert "Converse com sua planilha" in output
    assert "gemini-2.5-flash" in output


def test_print_visual_insights_runs_without_error():
    console = Console(record=True, width=140)
    print_visual_insights(console, _visual_snapshot())
    output = console.export_text()
    assert "overview da planilha" in output
    assert "Abas principais" in output


def test_wants_visual_summary_detects_sheet_questions():
    assert wants_visual_summary("me da um overview da planilha e das abas")
    assert not wants_visual_summary("qual e a capital da franca?")


def test_render_assistant_message_returns_chat_group():
    rendered = render_assistant_message("Ola")
    assert rendered is not None
