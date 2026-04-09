from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import ai_agent
from ai_agent import ask, build_prompt, choose_default_model, list_available_models, resolve_model_name


def test_build_prompt_includes_context():
    context = "ABA: Revenue\n- colunas: month, revenue"
    insights = "- Arquivo xlsx com 2 abas"
    question = "Qual aba tem mais linhas?"
    prompt = build_prompt(context, insights, question)
    assert "Revenue" in prompt
    assert "Qual aba tem mais linhas?" in prompt
    assert "Arquivo xlsx" in prompt
    assert "analista humano" in prompt


def test_build_prompt_includes_no_hallucination_instruction():
    prompt = build_prompt("ctx", "insights", "q?")
    assert "somente" in prompt.lower() or "nao invente" in prompt.lower()


def test_ask_is_a_generator():
    mock_chunk = MagicMock()
    mock_chunk.text = "resposta"
    mock_client = MagicMock()
    mock_client.models.generate_content_stream.return_value = iter([mock_chunk])

    with patch("ai_agent._get_client", return_value=mock_client):
        chunks = list(ask("ctx", "insights", "pergunta?", model_name="gemini-2.5-flash"))

    assert chunks == ["resposta"]


def test_ask_returns_soft_notice_when_stream_breaks_after_partial_output():
    mock_client = MagicMock()

    def broken_stream(**kwargs):
        yield SimpleNamespace(text="primeira parte")
        raise RuntimeError("provider failure")

    mock_client.models.generate_content_stream.side_effect = broken_stream

    with patch("ai_agent._get_client", return_value=mock_client):
        chunks = list(ask("ctx", "insights", "pergunta?", model_name="gemini-2.5-flash"))

    assert chunks[0] == "primeira parte"
    assert "interrompida pela API" in chunks[-1]


def test_list_available_models_filters_and_sorts():
    ai_agent._MODEL_CACHE = None
    mock_client = MagicMock()
    mock_client.models.list.return_value = [
        SimpleNamespace(name="models/gemini-2.0-flash", supported_actions=["generateContent"]),
        SimpleNamespace(name="models/gemini-2.5-pro", supported_actions=["generateContent"]),
        SimpleNamespace(name="models/gemini-2.5-flash", supported_actions=["generateContent"]),
        SimpleNamespace(name="models/gemini-2.5-flash-preview-tts", supported_actions=["generateContent"]),
        SimpleNamespace(name="models/text-bison", supported_actions=["generateContent"]),
    ]

    with patch("ai_agent._get_client", return_value=mock_client):
        models = list_available_models(refresh=True)

    assert models == ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]


def test_choose_default_model_prefers_best_flash_variant():
    models = ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-2.5-flash"]
    assert choose_default_model(models) == "gemini-2.5-flash"


def test_resolve_model_name_falls_back_when_requested_is_unavailable():
    models = ["gemini-2.5-flash", "gemini-2.0-flash"]
    assert resolve_model_name("gemini-3-flash-preview", models) == "gemini-2.5-flash"
