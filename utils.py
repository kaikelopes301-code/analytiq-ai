SEPARATOR = "─" * 60


def format_answer(text: str) -> str:
    """Wrap an AI answer with visual separators."""
    return f"\n{SEPARATOR}\n{text}\n{SEPARATOR}\n"


def format_insights_header() -> str:
    """Return the header shown before auto-insights."""
    return f"\nInsights automáticos:\n{SEPARATOR}"


def truncate_text(text: str, max_chars: int = 4000) -> str:
    """Truncate long text to avoid exceeding API limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def print_welcome(filepath: str) -> None:
    """Print welcome message after loading a CSV."""
    print(f"\nDados carregados: {filepath}")
    print("Digite sua pergunta (ou 'sair' para encerrar)\n")
