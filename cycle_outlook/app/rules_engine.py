from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .storage import Storage
from .util_text import contains_decision_terms, contains_urgent_terms, extract_email_domain

CATEGORIES = {"CRISES", "DECISIONS", "A_LIRE"}


@dataclass
class RuleResult:
    category: str
    reasons: List[str]
    rule_id: Optional[int] = None


class RulesEngine:
    def __init__(self, storage: Optional[Storage] = None) -> None:
        self.storage = storage or Storage()

    def match_rules(self, email: Dict[str, Any]) -> Optional[RuleResult]:
        rules = self.storage.get_rules()
        sender_email = (email.get("sender_email") or "").lower()
        sender_name = (email.get("sender_name") or "").lower()
        subject = (email.get("subject") or "").lower()
        body = (email.get("body_excerpt") or "").lower()
        domain = extract_email_domain(sender_email)

        for rule in rules:
            pattern = (rule.get("pattern") or "").lower()
            rtype = rule.get("type")
            if not pattern:
                continue
            if rtype == "sender_exact" and sender_email == pattern:
                return RuleResult(rule["category"], [f"Expediteur exact: {pattern}"], rule["id"])
            if rtype == "sender_domain" and domain == pattern:
                return RuleResult(rule["category"], [f"Domaine expediteur: {pattern}"], rule["id"])
            if rtype == "sender_name" and pattern in sender_name:
                return RuleResult(rule["category"], [f"Nom expediteur contient: {pattern}"], rule["id"])
            if rtype == "keyword_subject" and pattern in subject:
                return RuleResult(rule["category"], [f"Mot-cle objet: {pattern}"], rule["id"])
            if rtype == "keyword_body" and pattern in body:
                return RuleResult(rule["category"], [f"Mot-cle corps: {pattern}"], rule["id"])
            if rtype == "deadline" and (pattern in subject or pattern in body):
                return RuleResult(rule["category"], [f"Indicateur echeance: {pattern}"], rule["id"])
            if rtype == "sensitive_sender" and (sender_email == pattern or domain == pattern):
                return RuleResult(rule["category"], [f"Expediteur sensible: {pattern}"], rule["id"])
        return None

    def apply_heuristics(self, email: Dict[str, Any]) -> Optional[RuleResult]:
        text = f"{email.get('subject') or ''} {email.get('body_excerpt') or ''}"
        if contains_urgent_terms(text):
            return RuleResult("CRISES", ["Indicateurs d'urgence detectes"], None)
        if contains_decision_terms(text):
            return RuleResult("DECISIONS", ["Demande de validation/decision"], None)
        return None

    def classify(self, email: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        rule_result = self.match_rules(email)
        if rule_result:
            return rule_result.category, {
                "source": "RULE",
                "reasons": rule_result.reasons,
                "rule_id": rule_result.rule_id,
            }
        heuristic = self.apply_heuristics(email)
        if heuristic:
            return heuristic.category, {
                "source": "HEURISTIC",
                "reasons": heuristic.reasons,
            }
        return "A_LIRE", {"source": "DEFAULT", "reasons": ["Aucune regle ni heuristique"]}
