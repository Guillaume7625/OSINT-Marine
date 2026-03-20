from typing import Any, Dict, Tuple

from .genial_client import GenialClient
from .rules_engine import RulesEngine


class Classifier:
    def __init__(self, storage=None) -> None:
        self.rules_engine = RulesEngine(storage)
        self.genial = GenialClient(storage)

    def classify(self, email: Dict[str, Any], consignes: str) -> Tuple[str, Dict[str, Any]]:
        rule_result = self.rules_engine.match_rules(email)
        if rule_result:
            return rule_result.category, {
                "source": "RULE",
                "reasons": rule_result.reasons,
                "rule_id": rule_result.rule_id,
            }

        if self.genial.is_enabled():
            payload = {
                "instructions_utilisateur": consignes,
                "from": email.get("sender_email"),
                "to_cc": email.get("to_cc"),
                "subject": email.get("subject"),
                "received_time_iso": email.get("received_time"),
                "body_excerpt": email.get("body_excerpt"),
            }
            result = self.genial.classify(payload)
            if result.category:
                return result.category, {
                    "source": "GENIAL",
                    "reasons": result.reasons or [],
                    "confidence": result.confidence,
                }

        heuristic = self.rules_engine.apply_heuristics(email)
        if heuristic:
            return heuristic.category, {
                "source": "HEURISTIC",
                "reasons": heuristic.reasons,
            }
        return "A_LIRE", {"source": "DEFAULT", "reasons": ["Aucune regle ni heuristique"]}
