from pathlib import Path
from typing import Any, Callable
import unicodedata

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

console = Console()

_VISUAL_KEYWORDS = (
    "insight",
    "insights",
    "resumo",
    "overview",
    "painel",
    "dashboard",
    "aba",
    "abas",
    "sheet",
    "sheets",
    "coluna",
    "colunas",
    "formula",
    "formulas",
    "estrutura",
)


def print_header(console: Console, model: str, filepath: str) -> None:
    """Print a compact fallback header with model and file info."""
    console.print()
    console.print(Rule("[bold]analytiq.ai[/bold]", style="bright_black"))
    console.print(f"  [dim]{model} · {filepath}[/dim]")
    console.print()


def print_welcome(console: Console, filepath: str, model: str, snapshot: dict) -> None:
    """Print a minimal, centered welcome screen."""
    dataset_name = Path(filepath).name
    brand = Text("analytiq.ai", style="bold bright_cyan", justify="center")
    title = Text("Bem-vindo de volta", style="bold white", justify="center")
    accent = Text("Converse com sua planilha", style="white", justify="center")
    context = Text(
        f"{snapshot['sheet_count']} abas · {snapshot['total_rows']} linhas uteis · {snapshot['total_formulas']} formulas",
        style="dim",
        justify="center",
    )
    focus = Text(
        f"aba principal: {snapshot['primary_sheet'] or 'n/a'}",
        style="grey62",
        justify="center",
    )
    fileline = Text(filepath, style="bright_black", justify="center")
    datasetline = Text(dataset_name, style="grey62", justify="center")
    modelline = Text(f"modelo atual: {model}", style="dim", justify="center")
    helptext = Text(
        "Pergunte sobre abas, colunas, formulas e dados ou use /insights, /modelos, /ajuda.",
        style="dim",
        justify="center",
    )

    content = Group(
        Text(" ", justify="center"),
        Text(" ", justify="center"),
        brand,
        Text(" ", justify="center"),
        title,
        accent,
        Text(" ", justify="center"),
        context,
        focus,
        datasetline,
        fileline,
        modelline,
        Text(" ", justify="center"),
        helptext,
        Text(" ", justify="center"),
    )
    console.print()
    console.print(Align.center(content, vertical="middle"))
    console.print()


def print_help(console: Console) -> None:
    """Print chat commands for the terminal interface."""
    rows = Table.grid(expand=False, padding=(0, 2))
    rows.add_column(style="bold bright_cyan")
    rows.add_column(style="dim")
    rows.add_row("/insights", "abre um resumo estrutural da planilha")
    rows.add_row("/modelos", "lista os modelos Gemini disponiveis para esta chave")
    rows.add_row("/modelo <id>", "troca o modelo atual sem reiniciar a sessao")
    rows.add_row("/modelo auto", "escolhe automaticamente o melhor fallback disponivel")
    rows.add_row("/limpar", "limpa a tela e volta para a tela inicial")
    rows.add_row("/sair", "encerra a sessao")
    console.print(Panel(rows, title="Comandos", border_style="bright_black", padding=(1, 2)))
    console.print()


def print_model_selector(
    console: Console,
    current_model: str,
    available_models: list[str],
    recommended_model: str,
) -> None:
    """Render the list of models that can be selected in-session."""
    body = Table.grid(expand=False, padding=(0, 1))
    body.add_column(style="bold white")
    body.add_column(style="dim")
    for model in available_models:
        badge = "atual" if model == current_model else ("recomendado" if model == recommended_model else "")
        label = f"[bold bright_cyan]{model}[/bold bright_cyan]" if model == current_model else model
        body.add_row(label, badge)

    if not available_models:
        body.add_row("Nenhum modelo listado", "a API nao retornou opcoes nesta sessao")

    footer = Text(
        "Use /modelo <id> para trocar. Se um preview nao estiver liberado para a sua chave, o app mantem fallback.",
        style="dim",
    )
    console.print(
        Panel(
            Group(body, Text(""), footer),
            title="Modelos Gemini",
            border_style="bright_black",
            padding=(1, 2),
        )
    )
    console.print()


def print_visual_insights(console: Console, visual_snapshot: dict) -> None:
    """Render a generic workbook summary for the /insights command."""
    console.print("  [dim]overview da planilha[/dim]")
    console.print()

    cards = []
    for card in visual_snapshot["cards"]:
        cards.append(
            Panel(
                Group(
                    Text(card["caption"], style="dim"),
                    Text(str(card["value"]), style="bold white"),
                ),
                title=card["label"],
                border_style="bright_cyan",
                padding=(1, 2),
            )
        )
    console.print(Columns(cards, expand=True, equal=True))
    console.print()

    sheet_table = Table(
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold bright_cyan",
        expand=True,
    )
    sheet_table.add_column("Aba", style="bold white")
    sheet_table.add_column("Linhas", justify="right")
    sheet_table.add_column("Colunas", justify="right")
    sheet_table.add_column("Numericas", justify="right")
    sheet_table.add_column("Datas", justify="right")
    sheet_table.add_column("Formulas", justify="right")
    sheet_table.add_column("Destaque")
    for sheet in visual_snapshot["sheets"]:
        sheet_table.add_row(
            sheet["name"],
            str(sheet["rows"]),
            str(sheet["columns"]),
            str(sheet["numeric_columns"]),
            str(sheet["date_columns"]),
            str(sheet["formula_count"]),
            sheet["notes"],
        )

    highlights = Text()
    for line in visual_snapshot["highlights"]:
        highlights.append(f"* {line}\n", style="white")
    if highlights.plain.endswith("\n"):
        highlights.rstrip()

    console.print(
        Columns(
            [
                Panel(sheet_table, title="Abas principais", border_style="bright_black", padding=(1, 1)),
                Panel(highlights, title="Highlights", border_style="bright_black", padding=(1, 2)),
            ],
            expand=True,
            equal=True,
        )
    )
    console.print()


def make_reasoning_panel(insights: str) -> Panel:
    """Build the legacy reasoning panel from insight text."""
    return Panel(insights, title="Raciocinio", border_style="dim", padding=(0, 1))


def wants_visual_summary(question: str) -> bool:
    """Detect when the user is asking for workbook structure or overview views."""
    normalized = "".join(
        char
        for char in unicodedata.normalize("NFD", question.lower())
        if unicodedata.category(char) != "Mn"
    )
    return any(keyword in normalized for keyword in _VISUAL_KEYWORDS)


def render_assistant_message(message: str):
    """Render the assistant response in a chat-like layout."""
    return Group(
        Text("  analytiq >", style="bold bright_cyan"),
        Markdown(message),
    )


def truncate_text(text: str, max_chars: int = 4000) -> str:
    """Truncate long text to avoid exceeding API limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def run_with_spinner(console: Console, message: str, fn: Callable[[], Any]) -> Any:
    """Run fn() while showing a spinner. Returns fn's result."""
    with console.status(f"[dim]{message}[/dim]", spinner="dots"):
        return fn()
