from ai_agent import build_prompt


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
