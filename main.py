import sys
from data_loader import load_csv, get_column_summary
from analyzer import compute_basic_stats, generate_insights
from ai_agent import ask
from utils import format_answer, format_insights_header, print_welcome


def build_context(df, column_summary: dict, stats: dict) -> str:
    """Assemble a text context string from DataFrame metadata and stats."""
    lines = [
        f"Dataset: {column_summary['shape'][0]} linhas, {column_summary['shape'][1]} colunas.",
        f"Colunas: {', '.join(column_summary['columns'])}",
        f"Tipos: {column_summary['dtypes']}",
        "",
        "Estatísticas por coluna:",
    ]
    for col, s in stats.items():
        lines.append(
            f"  {col}: mean={s['mean']:.2f}, std={s['std']:.2f}, "
            f"min={s['min']:.2f}, max={s['max']:.2f}"
        )
    lines.append("")
    lines.append("Primeiras linhas:")
    lines.append(df.head(5).to_string(index=False))
    return "\n".join(lines)


def run(filepath: str) -> None:
    """Main loop: load data, show insights, answer questions."""
    df = load_csv(filepath)
    column_summary = get_column_summary(df)
    stats = compute_basic_stats(df)
    insights = generate_insights(df)
    context = build_context(df, column_summary, stats)

    print_welcome(filepath)
    print(format_insights_header())
    print(insights)

    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté mais!")
            break

        if question.lower() in ("sair", "exit", "quit"):
            print("Até mais!")
            break

        if not question:
            continue

        answer = ask(context, insights, question)
        print(format_answer(answer))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python main.py <caminho_para_o_csv>")
        print("Exemplo: python main.py data/sample.csv")
        sys.exit(1)

    run(sys.argv[1])
