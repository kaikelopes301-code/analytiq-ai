# ai_agent.py
import os
from typing import Generator
import google.generativeai as genai
from dotenv import load_dotenv
from utils import truncate_text

load_dotenv()


def _get_model():
    """Initialize and return the Gemini model."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY não encontrada no .env")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")


def build_prompt(context: str, insights: str, question: str) -> str:
    """Assemble the full prompt sent to Gemini."""
    return f"""Você é um analista de dados sênior. Responda APENAS com base nos dados fornecidos.
Se não houver informação suficiente, diga isso claramente. Não invente dados.
Seja analítico, direto e aponte causas prováveis quando os dados sugerirem.

=== RESUMO DOS DADOS ===
{truncate_text(context, max_chars=2000)}

=== INSIGHTS AUTOMÁTICOS ===
{truncate_text(insights, max_chars=1000)}

=== PERGUNTA DO USUÁRIO ===
{question}

Responda em português, de forma clara e objetiva."""


def ask(context: str, insights: str, question: str) -> Generator[str, None, None]:
    """Stream the Gemini response chunk by chunk."""
    model = _get_model()
    prompt = build_prompt(context, insights, question)
    try:
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"Erro ao consultar a IA: {e}"
