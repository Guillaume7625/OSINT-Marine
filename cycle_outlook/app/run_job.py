import argparse
import sys
from typing import Any, Dict, List, Optional

from .classifier import Classifier
from .logging_config import configure_logging
from .outlook_client import OutlookClient
from .storage import Storage
from .util_text import hash_text

FOLDER_MAP = {"CRISES": "Crises", "DECISIONS": "Décisions", "A_LIRE": "À lire"}


def run_job(limit: int, days_window: int, dry_run: bool) -> Dict[str, Any]:
    storage = Storage()
    classifier = Classifier(storage)
    outlook = OutlookClient()

    lock_id = storage.acquire_lock("job", ttl_seconds=900)
    if not lock_id:
        return {"status": "locked", "message": "Un traitement est déjà en cours"}

    run_id = storage.create_run(dry_run=dry_run, limit_count=limit, days_window=days_window)
    storage.append_log("INFO", "run_started", run_id, {"dry_run": dry_run, "limit": limit, "days": days_window})

    processed: List[Dict[str, Any]] = []
    errors = 0
    moved = 0
    try:
        consignes = storage.get_latest_consignes()
        items = outlook.fetch_messages(limit=limit, days_window=days_window)
        for item in items:
            message: Dict[str, Any] = {
                "entry_id": item.entry_id,
                "subject": item.subject,
                "sender_email": item.sender_email,
                "sender_name": item.sender_name,
                "received_time": item.received_time,
                "body_excerpt": item.body_excerpt,
                "body_hash": hash_text(item.body_excerpt),
                "to_cc": item.to_cc,
                "attachments": item.attachments,
            }
            category, explain = classifier.classify(message, consignes)
            message["category"] = category
            message["explain"] = explain
            outcome = "preview"
            if not dry_run:
                try:
                    folder = FOLDER_MAP.get(category, "À lire")
                    outlook.move_message(item.entry_id, folder)
                    outcome = f"moved:{folder}"
                    moved += 1
                except Exception as exc:
                    errors += 1
                    outcome = f"move_failed:{exc}"
            message["outcome"] = outcome
            storage.save_message(run_id, message)
            processed.append(message)
        storage.finish_run(run_id, "ok", total_count=len(processed), moved_count=moved, errors_count=errors)
        storage.append_log("INFO", "run_finished", run_id, {"total": len(processed), "moved": moved, "errors": errors})
        status = "ok"
    except Exception as exc:
        errors += 1
        storage.finish_run(run_id, "error", total_count=len(processed), moved_count=moved, errors_count=errors)
        storage.append_log("ERROR", "run_failed", run_id, {"error": str(exc)})
        status = "error"
    finally:
        storage.release_lock("job", lock_id)

    return {"status": status, "run_id": run_id, "messages": processed, "moved": moved, "errors": errors}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Cycle-like Outlook triage job")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--dry-run", type=str, default="true")
    args = parser.parse_args(argv)
    dry_run = str(args.dry_run).lower() in ("1", "true", "yes")

    configure_logging()
    result = run_job(limit=args.limit, days_window=args.days, dry_run=dry_run)
    print(result)
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
