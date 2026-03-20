from app.genial_client import GenialClient


def test_mapping_with_defaults():
    client = GenialClient()
    data = {"data": {"category": "DECISIONS", "confidence": 0.8, "reasons": ["ok"]}}
    mapping = {
        "category_path": "data.category",
        "confidence_path": "data.confidence",
        "reasons_path": "data.reasons",
        "defaults": {"category": "A_LIRE", "confidence": None, "reasons": []},
    }
    category, confidence, reasons, mapped = client._map_response(data, mapping)
    assert category == "DECISIONS"
    assert confidence == 0.8
    assert reasons == ["ok"]
    assert mapped["category"] == "DECISIONS"


def test_mapping_invalid_category():
    client = GenialClient()
    data = {"data": {"category": "AUTRE"}}
    mapping = {"category_path": "data.category", "defaults": {"category": "A_LIRE"}}
    category, confidence, reasons, mapped = client._map_response(data, mapping)
    assert category is None
    assert mapped["category"] is None
