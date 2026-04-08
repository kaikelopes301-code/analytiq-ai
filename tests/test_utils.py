from utils import format_answer, format_insights_header, truncate_text


def test_format_answer_wraps_text():
    result = format_answer("This is a response.")
    assert "This is a response." in result


def test_format_insights_header_returns_string():
    result = format_insights_header()
    assert isinstance(result, str)
    assert len(result) > 0


def test_truncate_text_limits_length():
    long_text = "a" * 1000
    result = truncate_text(long_text, max_chars=100)
    assert len(result) <= 103  # 100 + "..."
