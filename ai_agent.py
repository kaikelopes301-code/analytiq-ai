import os
from typing import Generator

from dotenv import load_dotenv
from google import genai

from utils import truncate_text

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"
PREFERRED_MODELS = (
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
)
_MODEL_CACHE: list[str] | None = None


def _normalize_model_name(model_name: str | None) -> str:
    """Normalize API model names such as models/gemini-2.5-flash."""
    if not model_name:
        return ""
    normalized = model_name.strip()
    return normalized[7:] if normalized.startswith("models/") else normalized


def _sort_models(models: list[str]) -> list[str]:
    """Sort known models with preferred Gemini Flash variants first."""
    unique_models = list(dict.fromkeys(_normalize_model_name(model) for model in models if model))

    def rank(name: str):
        if name in PREFERRED_MODELS:
            return (0, PREFERRED_MODELS.index(name), name)
        if name.startswith("gemini-"):
            return (1, 0, name)
        if name.startswith("gemma-"):
            return (2, 0, name)
        return (3, 0, name)

    return sorted(unique_models, key=rank)


def _get_client():
    """Initialize and return the Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY nao encontrada no .env")
    return genai.Client(api_key=api_key)


def list_available_models(refresh: bool = False) -> list[str]:
    """List content-generation models available to the current API key."""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None and not refresh:
        return list(_MODEL_CACHE)

    client = _get_client()
    discovered = []
    for model in client.models.list():
        name = _normalize_model_name(getattr(model, "name", ""))
        actions = set(getattr(model, "supported_actions", []) or [])
        if not name or "generateContent" not in actions:
            continue
        if not (name.startswith("gemini-") or name.startswith("gemma-")):
            continue
        if any(blocked in name for blocked in ("image", "tts", "embedding", "aqa", "computer-use")):
            continue
        discovered.append(name)

    _MODEL_CACHE = _sort_models(discovered)
    return list(_MODEL_CACHE)


def choose_default_model(available_models: list[str] | None = None) -> str:
    """Choose the best available default model, favoring Flash variants."""
    models = _sort_models(available_models or [])
    for candidate in PREFERRED_MODELS:
        if candidate in models:
            return candidate
    return models[0] if models else MODEL_NAME


def resolve_model_name(requested_model: str | None, available_models: list[str] | None = None) -> str:
    """Resolve the effective model while tolerating unknown startup state."""
    requested = _normalize_model_name(requested_model)
    models = _sort_models(available_models or [])
    if requested and (not models or requested in models):
        return requested
    return choose_default_model(models)


def build_prompt(context: str, insights: str, question: str) -> str:
    """Assemble the runtime prompt for spreadsheet QA."""
    return f"""Voce e um analista senior de dados que conversa com naturalidade sobre planilhas.

REGRAS:
- Responda SOMENTE com base no contexto extraido do arquivo em runtime.
- O arquivo pode ter multiplas abas, formulas, colunas vazias e tabelas com estruturas diferentes.
- Quando citar dados, mencione a aba e as colunas sempre que isso ajudar.
- Se o contexto mostrar formulas, voce pode explicar a logica delas, mas nao invente valores nao presentes.
- Se uma resposta depender de calculo que nao apareceu no contexto, diga isso claramente.
- Se houver pouca evidencia para uma conclusao, seja explicito.
- Escreva como um analista humano explicando para outra pessoa, e nao como um dump tecnico de metadados.
- Se a pergunta for aberta, comece com a resposta principal em 1 ou 2 frases e depois explique o por que.
- Se a pergunta pedir interpretacao, conecte estrutura, dados e formulas em linguagem natural.
- Evite listar tudo da planilha sem necessidade. Selecione apenas o que ajuda a responder.

CONTEXTO DO ARQUIVO:
{truncate_text(context, max_chars=9000)}

INSIGHTS PRE-CALCULADOS:
{truncate_text(insights, max_chars=1200)}

PERGUNTA: {question}

Responda em portugues, de forma natural, clara e pragmatica."""


def _stream_content(client, model_name: str, prompt: str) -> Generator[str, None, None]:
    """Stream chunks from the selected model."""
    for chunk in client.models.generate_content_stream(
        model=model_name,
        contents=prompt,
    ):
        if chunk.text:
            yield chunk.text


def ask(
    context: str,
    insights: str,
    question: str,
    model_name: str | None = None,
) -> Generator[str, None, None]:
    """Stream the Gemini response chunk by chunk."""
    client = _get_client()
    prompt = build_prompt(context, insights, question)
    selected_model = _normalize_model_name(model_name) or MODEL_NAME
    emitted_any_chunk = False
    try:
        for chunk in _stream_content(client, selected_model, prompt):
            emitted_any_chunk = True
            yield chunk
    except Exception as exc:
        if selected_model != MODEL_NAME:
            yield f"_Aviso: `{selected_model}` nao respondeu nesta conta. Usando `{MODEL_NAME}`._\n\n"
            try:
                for chunk in _stream_content(client, MODEL_NAME, prompt):
                    emitted_any_chunk = True
                    yield chunk
                return
            except Exception as fallback_exc:
                if emitted_any_chunk:
                    yield "\n\n_(A resposta foi interrompida pela API. Tente novamente para aprofundar.)_"
                    return
                yield f"Erro ao consultar a IA: {fallback_exc}"
                return
        if emitted_any_chunk:
            yield "\n\n_(A resposta foi interrompida pela API. Tente novamente para aprofundar.)_"
            return
        yield f"Erro ao consultar a IA: {exc}"
