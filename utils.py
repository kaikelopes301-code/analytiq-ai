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
    "dashboard",
    "painel",
    "metrica",
    "metricas",
    "mrr",
    "receita",
    "clientes",
    "cliente",
    "churn",
    "nps",
    "cac",
    "ltv",
    "margem",
    "performance",
    "overview",
    "grafico",
    "grafico",
    "visual",
)


def print_header(console: Console, model: str, filepath: str) -> None:
    """Print a compact fallback header with model and file info."""
    console.print()
    console.print(Rule("[bold]analytiq.ai[/bold]", style="bright_black"))
    console.print(f"  [dim]{model} · {filepath}[/dim]")
    console.print()


def _chg(val, unit: str, decimals: int = 1, good_up: bool = True) -> str:
    """Format a change value with directional arrow and color."""
    if val is None or (isinstance(val, float) and val != val):
        return "[dim]n/a[/dim]"
    if abs(val) < 0.005:
        return "[dim]= estavel[/dim]"
    up = val > 0
    good = up == good_up
    color = "green" if good else "red"
    arrow = "alta" if up else "queda"
    sign = "+" if up else ""
    return f"[{color}]{arrow} {sign}{val:.{decimals}f}{unit}[/{color}]"


def _format_metric(value: float, format_name: str) -> str:
    """Format a metric value for cards and trends."""
    if format_name == "currency":
        return f"${value:,.0f}"
    if format_name == "percent":
        return f"{value:.2f}%"
    if format_name == "ratio":
        return f"{value:.1f}x"
    if format_name == "integer":
        return f"{int(value):,}"
    return str(value)


def _sparkline(values: list[float]) -> str:
    """Render a compact ASCII sparkline."""
    if not values:
        return ""
    glyphs = "._-:=+#"
    low = min(values)
    high = max(values)
    if high == low:
        return glyphs[3] * len(values)
    return "".join(
        glyphs[round((value - low) / (high - low) * (len(glyphs) - 1))]
        for value in values
    )


def print_dashboard(console: Console, snapshot: dict) -> None:
    """Print a compact metrics dashboard with month-over-month changes."""
    period = snapshot["period"]
    months = snapshot["months"]
    console.print(f"  [dim]{period} · {months} meses de dados[/dim]")
    console.print()

    table = Table(
        box=box.SIMPLE,
        show_header=False,
        show_edge=False,
        padding=(0, 4, 0, 0),
        expand=False,
    )
    for _ in range(4):
        table.add_column(min_width=16, justify="left", no_wrap=True)

    def label(text):
        return f"[dim]{text}[/dim]"

    def val(text):
        return f"[bold white]{text}[/bold white]"

    table.add_row(label("MRR"), label("Clientes"), label("Churn Rate"), label("NPS"))
    table.add_row(
        val(f"${snapshot['mrr']:,.0f}"),
        val(f"{snapshot['customers']:,}"),
        val(f"{snapshot['churn_rate']:.2f}%"),
        val(str(snapshot["nps"])),
    )
    table.add_row(
        _chg(snapshot["mrr_chg"], "%"),
        _chg(snapshot["customers_chg"], "%"),
        _chg(snapshot["churn_chg"], "pp", decimals=2, good_up=False),
        _chg(snapshot["nps_chg"], " pts", decimals=0),
    )
    table.add_row("", "", "", "")
    table.add_row(label("CAC"), label("LTV"), label("LTV / CAC"), label("Gross Margin"))
    table.add_row(
        val(f"${snapshot['cac']:,.0f}"),
        val(f"${snapshot['ltv']:,.0f}"),
        val(f"{snapshot['ltv_cac']:.1f}x"),
        val(f"{snapshot['gross_margin']:.1f}%"),
    )
    table.add_row(
        _chg(snapshot["cac_chg"], "%", good_up=False),
        _chg(snapshot["ltv_chg"], "%"),
        _chg(snapshot["ltv_cac_chg"], "x"),
        _chg(snapshot["gross_margin_chg"], "pp"),
    )

    console.print(table)
    console.print(Rule(style="bright_black"))
    console.print()


def print_welcome(console: Console, filepath: str, model: str, snapshot: dict) -> None:
    """Print a minimal, centered welcome screen."""
    dataset_name = Path(filepath).name

    brand = Text("analytiq.ai", style="bold bright_cyan", justify="center")
    title = Text("Bem-vindo de volta", style="bold white", justify="center")
    accent = Text("Converse com seus dados", style="white", justify="center")
    context = Text(
        f"{snapshot['months']} meses carregados · último período {snapshot['period']}",
        style="dim",
        justify="center",
    )
    fileline = Text(filepath, style="bright_black", justify="center")
    datasetline = Text(dataset_name, style="grey62", justify="center")
    modelline = Text(f"modelo atual: {model}", style="dim", justify="center")
    helptext = Text(
        "Pergunte qualquer coisa sobre os dados ou use /insights, /modelos, /ajuda.",
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
    rows.add_row("/insights", "abre o painel visual com métricas, tendências e highlights")
    rows.add_row("/modelos", "lista os modelos Gemini disponíveis para esta chave")
    rows.add_row("/modelo <id>", "troca o modelo atual sem reiniciar a sessão")
    rows.add_row("/modelo auto", "escolhe automaticamente o melhor fallback disponível")
    rows.add_row("/limpar", "limpa a tela e volta para a tela inicial")
    rows.add_row("/sair", "encerra a sessão")
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
        body.add_row("Nenhum modelo listado", "a API não retornou opções nesta sessão")

    footer = Text(
        "Use /modelo <id> para trocar. Se um preview não estiver liberado para a sua chave, o app mantém fallback.",
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
    """Render the richer visual board only when the user asks for it."""
    console.print(
        f"  [dim]painel visual · {visual_snapshot['period']} · {visual_snapshot['months']} meses[/dim]"
    )
    console.print()

    cards = []
    for card in visual_snapshot["cards"]:
        unit = card.get("change_unit", "%")
        decimals = card.get("change_decimals", 1)
        cards.append(
            Panel(
                Group(
                    Text(card["caption"], style="dim"),
                    Text(_format_metric(card["value"], card["format"]), style="bold white"),
                    Text.from_markup(_chg(card["change"], unit, decimals, card["good_up"])),
                ),
                title=card["label"],
                border_style="bright_cyan",
                padding=(1, 2),
            )
        )
    console.print(Columns(cards, expand=True, equal=True))
    console.print()

    trend_table = Table(
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold bright_cyan",
        expand=True,
    )
    trend_table.add_column("Métrica", style="bold white")
    trend_table.add_column("Tendência", ratio=2)
    trend_table.add_column("Atual", justify="right")
    trend_table.add_column("Variação", justify="right")
    for trend in visual_snapshot["trends"]:
        unit = trend.get("change_unit", "%")
        decimals = trend.get("change_decimals", 1)
        trend_table.add_row(
            trend["label"],
            f"{_sparkline(trend['series'])}  [dim]{trend['labels'][0]} to {trend['labels'][-1]}[/dim]",
            _format_metric(trend["current"], trend["format"]),
            _chg(trend["change"], unit, decimals, trend["good_up"]),
        )

    highlights = Text()
    for item in visual_snapshot["highlights"]:
        tone = "green" if item["tone"] == "positive" else "yellow"
        highlights.append(f"* {item['title']}: ", style=tone)
        highlights.append(item["body"])
        highlights.append("\n")
    if highlights.plain.endswith("\n"):
        highlights.rstrip()

    console.print(
        Columns(
            [
                Panel(trend_table, title="Momentum", border_style="bright_black", padding=(1, 1)),
                Panel(highlights, title="Highlights", border_style="bright_black", padding=(1, 2)),
            ],
            expand=True,
            equal=True,
        )
    )
    console.print()


def make_reasoning_panel(insights: str) -> Panel:
    """Build the legacy reasoning panel from pre-computed insight text."""
    return Panel(insights, title="Raciocínio", border_style="dim", padding=(0, 1))


def wants_visual_summary(question: str) -> bool:
    """Detect when the user is asking for metrics, dashboard, or insight views."""
    normalized = "".join(
        char
        for char in unicodedata.normalize("NFD", question.lower())
        if unicodedata.category(char) != "Mn"
    )
    return any(keyword in normalized for keyword in _VISUAL_KEYWORDS)


def render_assistant_message(message: str):
    """Render the assistant response in a chat-like layout."""
    return Group(
        Text("  analytiq ›", style="bold bright_cyan"),
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
