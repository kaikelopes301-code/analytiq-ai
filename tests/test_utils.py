from rich.console import Console
from rich.panel import Panel
from utils import (
    make_reasoning_panel,
    truncate_text,
    print_header,
)


def test_make_reasoning_panel_returns_panel():
    panel = make_reasoning_panel("- MRR: mean=50k\n- QUEDA em 'churn_rate'")
    assert isinstance(panel, Panel)


def test_truncate_text_limits_length():
    long_text = "a" * 1000
    result = truncate_text(long_text, max_chars=100)
    assert len(result) <= 103


def test_print_header_runs_without_error():
    console = Console(quiet=True)
    # should not raise
    print_header(console, "gemini-2.5-flash", "data/sample.csv")
