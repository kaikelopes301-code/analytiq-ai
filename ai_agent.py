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
        raise EnvironmentError("GEMINI_API_KEY não encontrada no .env")
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
    """Assemble the full prompt sent to Gemini."""
    return f"""Você é um analista de dados sênior especializado em métricas SaaS.

REGRAS:
- Responda SOMENTE com base nos dados abaixo. Nunca invente ou estime números.
- "Último mês", "mês passado" ou "mais recente" = o mês indicado em ÚLTIMO MÊS NOS DADOS.
- Cite sempre valores exatos e variações percentuais dos dados.
- Se identificar padrões relevantes além da pergunta, mencione em 1 linha.
- Se os dados não tiverem a informação solicitada, diga claramente.

{truncate_text(context, max_chars=3800)}

ALERTAS PRÉ-CALCULADOS:
{truncate_text(insights, max_chars=500)}

PERGUNTA: {question}

Responda em português, de forma direta. Vá ao ponto, cite os números."""


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
    try:
        yield from _stream_content(client, selected_model, prompt)
    except Exception as exc:
        if selected_model != MODEL_NAME:
            yield f"_Aviso: `{selected_model}` não respondeu nesta conta. Usando `{MODEL_NAME}`._\n\n"
            try:
                yield from _stream_content(client, MODEL_NAME, prompt)
                return
            except Exception as fallback_exc:
                yield f"Erro ao consultar a IA: {fallback_exc}"
                return
        yield f"Erro ao consultar a IA: {exc}"
