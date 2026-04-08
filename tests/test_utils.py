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
        "period": "2024-12",
        "months": 60,
        "cards": [
            {"label": "MRR", "value": 1178000, "change": 4.7, "format": "currency", "good_up": True, "caption": "fechamento de 2024-12"},
            {"label": "Clientes", "value": 8489, "change": 3.7, "format": "integer", "good_up": True, "caption": "base ativa"},
            {"label": "Churn", "value": 0.30, "change": 0.0, "format": "percent", "good_up": False, "change_unit": "pp", "change_decimals": 2, "caption": "saúde da retenção"},
            {"label": "NPS", "value": 70, "change": 2.0, "format": "integer", "good_up": True, "change_unit": " pts", "change_decimals": 0, "caption": "voz do cliente"},
            {"label": "CAC", "value": 428, "change": -0.9, "format": "currency", "good_up": False, "caption": "custo de aquisição"},
            {"label": "LTV / CAC", "value": 108.1, "change": 2.1, "format": "ratio", "good_up": True, "change_unit": "x", "caption": "eficiência unitária"},
        ],
        "trends": [
            {"label": "MRR", "series": [910000, 980000, 1030000, 1090000, 1125000, 1178000], "labels": ["2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"], "format": "currency", "current": 1178000, "change": 4.7, "good_up": True},
            {"label": "Clientes", "series": [7100, 7420, 7760, 8010, 8189, 8489], "labels": ["2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"], "format": "integer", "current": 8489, "change": 3.7, "good_up": True},
            {"label": "NPS", "series": [61, 63, 65, 67, 68, 70], "labels": ["2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"], "format": "integer", "current": 70, "change": 2.0, "good_up": True, "change_unit": " pts", "change_decimals": 0},
            {"label": "Churn", "series": [0.52, 0.46, 0.41, 0.36, 0.30, 0.30], "labels": ["2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"], "format": "percent", "current": 0.30, "change": 0.0, "good_up": False, "change_unit": "pp", "change_decimals": 2},
        ],
        "highlights": [
            {"title": "Receita", "tone": "positive", "body": "MRR fechou 2024-12 em 1.178.000, 4,7% acima do mês anterior."},
            {"title": "Retenção", "tone": "positive", "body": "Churn em 0,30% com NPS de 70 indica base saudável."},
            {"title": "Eficiência", "tone": "positive", "body": "CAC em 428 e LTV/CAC em 108,1x reforçam unit economics."},
        ],
    }


def test_make_reasoning_panel_returns_panel():
    text = "- MRR: mean=50k\n- QUEDA em 'churn_rate'"
    panel = make_reasoning_panel(text)
    assert isinstance(panel, Panel)
    assert panel.renderable == text
    assert panel.title == "Raciocínio"
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
    snapshot = {"months": 60, "period": "2024-12"}
    print_welcome(console, "data/sample.csv", "gemini-2.5-flash", snapshot)
    output = console.export_text()
    assert "Bem-vindo de volta" in output
    assert "Converse com seus dados" in output
    assert "gemini-2.5-flash" in output


def test_print_visual_insights_runs_without_error():
    console = Console(record=True, width=140)
    print_visual_insights(console, _visual_snapshot())
    output = console.export_text()
    assert "painel visual" in output
    assert "Momentum" in output


def test_wants_visual_summary_detects_dashboard_questions():
    assert wants_visual_summary("me dá um dashboard de churn e MRR")
    assert not wants_visual_summary("qual é a capital da França?")


def test_render_assistant_message_returns_chat_group():
    rendered = render_assistant_message("Olá")
    assert rendered is not None
