from typing import Callable, Any

from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

console = Console()


def print_header(console: Console, model: str, filepath: str) -> None:
    """Print the single-line context header."""
    console.print(f"\nanalytiq-ai  •  [dim]{model}[/dim]  •  [dim]{filepath}[/dim]\n")


def make_reasoning_panel(insights: str) -> Panel:
    """Build the Raciocínio panel from pre-computed insight text."""
    return Panel(insights, title="Raciocínio", border_style="dim", padding=(0, 1))


def truncate_text(text: str, max_chars: int = 4000) -> str:
    """Truncate long text to avoid exceeding API limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def run_with_spinner(console: Console, message: str, fn: Callable[[], Any]) -> Any:
    """Run fn() while showing a spinner. Returns fn's result."""
    with console.status(f"[dim]{message}[/dim]", spinner="dots"):
        return fn()
