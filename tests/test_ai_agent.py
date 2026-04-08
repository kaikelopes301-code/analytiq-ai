# tests/test_ai_agent.py
from ai_agent import build_prompt, ask
from unittest.mock import MagicMock, patch


def test_build_prompt_includes_context():
    context = "revenue mean=15000"
    insights = "- QUEDA em 'revenue' no período 4: -50.0%"
    question = "Teve queda?"
    prompt = build_prompt(context, insights, question)
    assert "revenue" in prompt
    assert "Teve queda?" in prompt
    assert "QUEDA" in prompt


def test_build_prompt_includes_no_hallucination_instruction():
    prompt = build_prompt("ctx", "insights", "q?")
    assert "não invente" in prompt.lower() or "apenas" in prompt.lower()


def test_ask_is_a_generator():
    mock_chunk = MagicMock()
    mock_chunk.text = "resposta"
    mock_model = MagicMock()
    mock_model.generate_content.return_value = iter([mock_chunk])

    with patch("ai_agent._get_model", return_value=mock_model):
        result = ask("ctx", "insights", "pergunta?")
        chunks = list(result)

    assert chunks == ["resposta"]
