from rich.console import Console
from rich.panel import Panel
from utils import (
    make_reasoning_panel,
    truncate_text,
    print_header,
)


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
