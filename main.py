# main.py
import sys
from rich.live import Live
from rich.text import Text
from data_loader import load_csv, get_column_summary
from analyzer import compute_basic_stats, generate_insights
from ai_agent import ask
from utils import console, print_header, make_reasoning_panel, run_with_spinner

MODEL = "gemini-2.5-flash"


def build_context(df, column_summary: dict, stats: dict) -> str:
    """Assemble a text context string from DataFrame metadata and stats."""
    lines = [
        f"Dataset: {column_summary['shape'][0]} linhas, {column_summary['shape'][1]} colunas.",
        f"Colunas: {', '.join(column_summary['columns'])}",
        "",
        "Estatísticas por coluna:",
    ]
    for col, s in stats.items():
        lines.append(
            f"  {col}: mean={s['mean']:.2f}, min={s['min']:.2f}, max={s['max']:.2f}"
        )
    lines.append("")
    lines.append("Primeiras linhas:")
    lines.append(df.head(5).to_string(index=False))
    return "\n".join(lines)


def run(filepath: str) -> None:
    """Main loop: load data, show reasoning panel, answer questions."""
    def load():
        df = load_csv(filepath)
        column_summary = get_column_summary(df)
        stats = compute_basic_stats(df)
        insights = generate_insights(df)
        context = build_context(df, column_summary, stats)
        return df, column_summary, stats, insights, context

    print_header(console, MODEL, filepath)
    df, column_summary, stats, insights, context = run_with_spinner(
        console, "Carregando...", load
    )

    console.print(make_reasoning_panel(insights))

    while True:
        try:
            question = console.input("\n[dim]>[/dim] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]até mais[/dim]")
            break

        if question.lower() in ("sair", "exit", "quit"):
            console.print("[dim]até mais[/dim]")
            break

        if not question:
            continue

        with console.status("[dim]Pensando...[/dim]", spinner="dots"):
            gen = ask(context, insights, question)
            first_chunk = next(gen, None)

        if first_chunk is None:
            continue

        accumulated = first_chunk
        console.print()
        with Live(Text(accumulated), console=console, refresh_per_second=15) as live:
            for chunk in gen:
                accumulated += chunk
                live.update(Text(accumulated))
        console.print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("uso: python main.py <caminho_para_o_csv>")
        console.print("exemplo: python main.py data/sample.csv")
        sys.exit(1)

    run(sys.argv[1])
