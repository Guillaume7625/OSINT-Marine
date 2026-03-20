import hashlib
import re
from typing import List

QUOTED_MARKERS = [
    "-----Original Message-----",
    "--- Original Message ---",
    "From:",
    "Sent:",
    "To:",
    "Subject:",
    "De :",
    "Envoye :",
    "A :",
    "Objet :",
]

SIGNATURE_MARKERS = [
    "-- ",
    "__",
    "Sent from my",
    "Envoye de mon",
]

URL_REGEX = re.compile(r"https?://\S+", re.IGNORECASE)
EMAIL_REGEX = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)


def clean_body(text: str) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    cleaned: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append("")
            continue
        if stripped.startswith(">"):
            continue
        if any(stripped.startswith(marker) for marker in QUOTED_MARKERS):
            break
        if any(stripped.startswith(marker) for marker in SIGNATURE_MARKERS):
            break
        cleaned.append(stripped)
    result = "\n".join(cleaned)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    return result


def truncate(text: str, max_len: int = 1000) -> str:
    if text is None:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def extract_urls(text: str) -> List[str]:
    return URL_REGEX.findall(text or "")


def extract_email_domain(email: str) -> str:
    if not email or "@" not in email:
        return ""
    return email.split("@", 1)[1].lower().strip()


def contains_urgent_terms(text: str) -> bool:
    terms = ["urgence", "urgent", "asap", "immediat", "immediate", "eod", "deadline", "echeance"]
    lower = (text or "").lower()
    return any(term in lower for term in terms)


def contains_decision_terms(text: str) -> bool:
    terms = ["pour validation", "arbitrage", "decision", "valider", "approbation"]
    lower = (text or "").lower()
    return any(term in lower for term in terms)


def sender_name_mismatch(sender_name: str, sender_email: str) -> bool:
    if not sender_name or not sender_email:
        return False
    domain = extract_email_domain(sender_email)
    if not domain:
        return False
    tokens = [re.sub(r"[^a-z0-9]", "", t.lower()) for t in sender_name.split()]
    tokens = [t for t in tokens if len(t) > 3]
    if not tokens:
        return False
    domain_parts = re.split(r"[.-]", domain)
    return not any(token in domain_parts or token in domain for token in tokens)


def is_lookalike_domain(domain: str) -> bool:
    if not domain:
        return False
    if domain.startswith("xn--"):
        return True
    confusables = set("0o1l5s2z8b")
    if any(char in confusables for char in domain):
        return True
    if domain.count("-") >= 2:
        return True
    return False
