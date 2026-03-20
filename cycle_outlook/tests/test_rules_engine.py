from app.rules_engine import RulesEngine
from app.storage import Storage


def make_storage(tmp_path):
    db_path = tmp_path / "test.db"
    return Storage(db_path=db_path)


def test_rule_match_sender_exact(tmp_path):
    storage = make_storage(tmp_path)
    storage.add_rule("sender_exact", "vip@example.com", "CRISES")
    engine = RulesEngine(storage)
    email = {
        "sender_email": "vip@example.com",
        "sender_name": "VIP",
        "subject": "hello",
        "body_excerpt": "test",
    }
    category, explain = engine.classify(email)
    assert category == "CRISES"
    assert explain["source"] == "RULE"
    assert explain["rule_id"]


def test_heuristic_decision(tmp_path):
    storage = make_storage(tmp_path)
    engine = RulesEngine(storage)
    email = {"subject": "pour validation", "body_excerpt": "merci", "sender_email": "a@b.com"}
    category, explain = engine.classify(email)
    assert category == "DECISIONS"
    assert explain["source"] == "HEURISTIC"


def test_default(tmp_path):
    storage = make_storage(tmp_path)
    engine = RulesEngine(storage)
    email = {"subject": "info", "body_excerpt": "lecture", "sender_email": "a@b.com"}
    category, explain = engine.classify(email)
    assert category == "A_LIRE"
    assert explain["source"] == "DEFAULT"
