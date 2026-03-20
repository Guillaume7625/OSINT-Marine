from app.summarizer import generate_summary, detect_suspects


def test_summary_sections():
    messages = [
        {
            "subject": "Urgent: action",
            "sender_email": "boss@example.com",
            "sender_name": "Boss",
            "received_time": "2024-01-01T10:00:00",
            "category": "CRISES",
            "body_excerpt": "ASAP http://example.com",
            "attachments": [],
        },
        {
            "subject": "Pour validation",
            "sender_email": "team@example.com",
            "sender_name": "Team",
            "received_time": "2024-01-01T12:00:00",
            "category": "DECISIONS",
            "body_excerpt": "merci",
            "attachments": [],
        },
    ]
    content, _ = generate_summary(messages)
    assert "Priorités (CRISES)" in content
    assert "Décisions" in content
    assert "À lire" in content


def test_detect_suspects_attachment():
    msg = {
        "subject": "Test",
        "sender_email": "test@examp1e.com",
        "sender_name": "Support",
        "body_excerpt": "ASAP http://example.com",
        "attachments": ["invoice.exe"],
    }
    reasons = detect_suspects(msg)
    assert any("Pièce jointe" in r for r in reasons)
