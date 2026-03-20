from app.util_text import clean_body, truncate


def test_clean_body_removes_quotes():
    raw = "Hello\n> quoted\nFrom: someone\nBody"
    cleaned = clean_body(raw)
    assert cleaned == "Hello"


def test_truncate():
    text = "a" * 10
    assert truncate(text, 5) == "aa..."
