import argparse
import sys

from rich.live import Live

from ai_agent import ask, choose_default_model, list_available_models, resolve_model_name
from analyzer import build_ai_context, build_visual_snapshot, generate_insights, get_snapshot
from data_loader import get_column_summary, load_csv
from utils import (
    console,
    print_help,
    print_model_selector,
    print_visual_insights,
    print_welcome,
    render_assistant_message,
    run_with_spinner,
    wants_visual_summary,
)


def _normalize_model_name(model_name: str | None) -> str:
    """Normalize model ids entered in the CLI or chat commands."""
    if not model_name:
        return ""
    normalized = model_name.strip()
    return normalized[7:] if normalized.startswith("models/") else normalized


def _refresh_models() -> list[str]:
    """Fetch the current model list while handling API failures gracefully."""
    try:
        return run_with_spinner(
            console,
            "Consultando modelos Gemini...",
            lambda: list_available_models(refresh=True),
        )
    except Exception as exc:
        console.print(f"  [yellow]Não consegui listar os modelos agora: {exc}[/yellow]")
        console.print()
        return []


def _handle_command(
    raw_question: str,
    filepath: str,
    snapshot: dict,
    visual_snapshot: dict,
    current_model: str,
    available_models: list[str],
) -> tuple[bool, bool, str, list[str]]:
    """Handle slash commands without sending them to the model."""
    command, _, arg = raw_question.partition(" ")
    command = command.lower()
    arg = _normalize_model_name(arg)

    if command in {"/sair", "/exit", "/quit"}:
        console.print("  [dim]até mais[/dim]")
        return True, True, current_model, available_models

    if command == "/ajuda":
        print_help(console)
        return True, False, current_model, available_models

    if command in {"/insights", "/dashboard", "/resumo"}:
        print_visual_insights(console, visual_snapshot)
        return True, False, current_model, available_models

    if command == "/limpar":
        console.clear()
        print_welcome(console, filepath, current_model, snapshot)
        return True, False, current_model, available_models

    if command == "/modelos":
        refreshed = _refresh_models()
        available_models = refreshed or available_models
        recommended_model = choose_default_model(available_models)
        print_model_selector(console, current_model, available_models, recommended_model)
        return True, False, current_model, available_models

    if command == "/modelo":
        if not arg:
            console.print(f"  [dim]modelo atual: {current_model}[/dim]")
            console.print()
            return True, False, current_model, available_models

        if arg == "auto":
            current_model = choose_default_model(available_models)
            console.print(f"  [dim]modelo ajustado para {current_model}[/dim]")
            console.print()
            return True, False, current_model, available_models

        if available_models and arg not in available_models:
            console.print(
                f"  [yellow]modelo `{arg}` não está disponível nesta chave. Use `/modelos` para ver a lista real.[/yellow]"
            )
            console.print()
            return True, False, current_model, available_models

        current_model = arg
        console.print(f"  [dim]modelo ajustado para {current_model}[/dim]")
        console.print()
        return True, False, current_model, available_models

    return False, False, current_model, available_models


def run(filepath: str, requested_model: str | None = None) -> None:
    """Load the dataset and run the terminal chat interface."""

    def load():
        df = load_csv(filepath)
        get_column_summary(df)
        insights = generate_insights(df)
        context = build_ai_context(df)
        snapshot = get_snapshot(df)
        visual_snapshot = build_visual_snapshot(df)
        try:
            available_models = list_available_models()
        except Exception:
            available_models = []
        return df, insights, context, snapshot, visual_snapshot, available_models

    _, insights, context, snapshot, visual_snapshot, available_models = run_with_spinner(
        console,
        "Carregando dados...",
        load,
    )

    current_model = resolve_model_name(requested_model, available_models)
    requested_model = _normalize_model_name(requested_model)

    console.clear()
    print_welcome(console, filepath, current_model, snapshot)
    if requested_model and requested_model != current_model:
        console.print(
            f"  [yellow]modelo `{requested_model}` indisponível nesta chave; usando `{current_model}`.[/yellow]"
        )
        console.print()

    while True:
        try:
            question = console.input("  [bold]você ›[/bold] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n  [dim]até mais[/dim]")
            break

        if question.lower() in ("sair", "exit", "quit"):
            console.print("  [dim]até mais[/dim]")
            break

        if not question:
            continue

        handled, should_exit, current_model, available_models = _handle_command(
            question,
            filepath,
            snapshot,
            visual_snapshot,
            current_model,
            available_models,
        )
        if should_exit:
            break
        if handled:
            continue

        if wants_visual_summary(question):
            print_visual_insights(console, visual_snapshot)

        with console.status("  [dim]pensando...[/dim]", spinner="dots"):
            gen = ask(context, insights, question, model_name=current_model)
            first_chunk = next(gen, None)

        if first_chunk is None:
            continue

        accumulated = first_chunk
        with Live(
            render_assistant_message(accumulated),
            console=console,
            refresh_per_second=12,
            vertical_overflow="visible",
        ) as live:
            for chunk in gen:
                accumulated += chunk
                live.update(render_assistant_message(accumulated))

        console.print()


def parse_args(argv: list[str]):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Análise de CSV com chat Gemini no terminal.")
    parser.add_argument("filepath", help="Caminho para o CSV")
    parser.add_argument("--model", help="Modelo Gemini a usar na sessão")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    run(args.filepath, requested_model=args.model)
