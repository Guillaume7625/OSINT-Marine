from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .util_text import (
    contains_urgent_terms,
    extract_email_domain,
    extract_urls,
    is_lookalike_domain,
    sender_name_mismatch,
)

RISKY_EXTENSIONS = {".exe", ".js", ".vbs", ".iso", ".lnk", ".html"}


def _parse_iso(dt_str: str) -> datetime:
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def detect_suspects(message: Dict[str, Any]) -> List[str]:
    reasons: List[str] = []
    sender_email = message.get("sender_email") or ""
    sender_name = message.get("sender_name") or ""
    domain = extract_email_domain(sender_email)
    if is_lookalike_domain(domain):
        reasons.append(f"Domaine suspect: {domain}")
    if sender_name_mismatch(sender_name, sender_email):
        reasons.append("Nom d'affichage discordant")
    if contains_urgent_terms(message.get("subject", "") + " " + message.get("body_excerpt", "")):
        if extract_urls(message.get("body_excerpt", "")):
            reasons.append("Urgence + lien")
    attachments = message.get("attachments") or []
    for name in attachments:
        lowered = name.lower()
        for ext in RISKY_EXTENSIONS:
            if lowered.endswith(ext):
                reasons.append(f"Pièce jointe à risque: {name}")
                break
    return reasons


def _line_for_message(message: Dict[str, Any], include_age: bool = False) -> str:
    subject = message.get("subject") or "(sans objet)"
    sender = message.get("sender_email") or message.get("sender_name") or ""
    received = message.get("received_time") or ""
    age = ""
    if include_age and received:
        dt = _parse_iso(received)
        delta_days = (datetime.now(timezone.utc) - dt).days
        age = f" — âge {delta_days}j"
    return f"- {subject} — {sender} ({received}){age}"


def generate_summary(messages: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    crises = [m for m in messages if m.get("category") == "CRISES"]
    decisions = [m for m in messages if m.get("category") == "DECISIONS"]
    to_read = [m for m in messages if m.get("category") == "A_LIRE"]

    suspects: List[Dict[str, Any]] = []
    for msg in messages:
        reasons = detect_suspects(msg)
        if reasons:
            suspects.append({"message": msg, "reasons": reasons})

    today = datetime.now().strftime("%Y-%m-%d")
    lines: List[str] = [f"# Résumé Cycle — {today}", ""]

    lines.append("## Priorités (CRISES)")
    if crises:
        for msg in crises:
            lines.append(_line_for_message(msg))
    else:
        lines.append("- Aucune")
    lines.append("")

    lines.append("## Décisions")
    if decisions:
        for msg in decisions:
            lines.append(_line_for_message(msg, include_age=True))
    else:
        lines.append("- Aucune")
    lines.append("")

    lines.append("## À lire")
    if to_read:
        for msg in to_read:
            lines.append(_line_for_message(msg))
    else:
        lines.append("- Aucun")
    lines.append("")

    lines.append("## Suspects")
    if suspects:
        for item in suspects:
            msg = item["message"]
            reasons = ", ".join(item["reasons"])
            subject = msg.get("subject") or "(sans objet)"
            sender = msg.get("sender_email") or msg.get("sender_name") or ""
            lines.append(f"- {subject} — {sender} [{reasons}]")
    else:
        lines.append("- Aucun")
    lines.append("")

    lines.append("## Stats")
    lines.append(f"- Total: {len(messages)}")
    lines.append(f"- Crises: {len(crises)}")
    lines.append(f"- Décisions: {len(decisions)}")
    lines.append(f"- À lire: {len(to_read)}")

    return "\n".join(lines), suspects
