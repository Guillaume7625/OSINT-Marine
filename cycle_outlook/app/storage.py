import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "app.db"
AUDIT_LOG_PATH = LOG_DIR / "audit.jsonl"
SEED_RULES_PATH = BASE_DIR / "rules_seed.json"

_DB_INIT_LOCK = threading.Lock()


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Storage:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else DB_PATH
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _DB_INIT_LOCK:
            self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    category TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consignes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS genial_config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    enabled INTEGER NOT NULL DEFAULT 0,
                    base_url TEXT,
                    path TEXT,
                    method TEXT,
                    allowlist_hosts_ports TEXT,
                    headers_json TEXT,
                    timeout_seconds INTEGER,
                    retries INTEGER,
                    request_template TEXT,
                    response_mapping_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    dry_run INTEGER NOT NULL,
                    limit_count INTEGER NOT NULL,
                    days_window INTEGER NOT NULL,
                    total_count INTEGER NOT NULL DEFAULT 0,
                    moved_count INTEGER NOT NULL DEFAULT 0,
                    errors_count INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    entry_id TEXT NOT NULL,
                    subject TEXT,
                    sender_email TEXT,
                    sender_name TEXT,
                    received_time TEXT,
                    category TEXT,
                    explain_json TEXT,
                    body_excerpt TEXT,
                    body_hash TEXT,
                    attachments_json TEXT,
                    outcome TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );

                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    level TEXT NOT NULL,
                    run_id TEXT,
                    event TEXT NOT NULL,
                    details_json TEXT
                );

                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    content_md TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(id)
                );

                CREATE TABLE IF NOT EXISTS locks (
                    name TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                """
            )
            conn.commit()
            self._ensure_columns(conn)
            self._seed_rules_if_empty(conn)
        finally:
            conn.close()

    def _ensure_columns(self, conn: sqlite3.Connection) -> None:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
        if "attachments_json" not in columns:
            conn.execute("ALTER TABLE messages ADD COLUMN attachments_json TEXT")
            conn.commit()

    def _seed_rules_if_empty(self, conn: sqlite3.Connection) -> None:
        try:
            row = conn.execute("SELECT COUNT(*) AS c FROM rules").fetchone()
            if row and row["c"] > 0:
                return
            if not SEED_RULES_PATH.exists():
                return
            with SEED_RULES_PATH.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            rules = data.get("rules", []) if isinstance(data, dict) else []
            for rule in rules:
                rtype = rule.get("type")
                pattern = rule.get("pattern")
                category = rule.get("category")
                enabled = int(bool(rule.get("enabled", True)))
                if not (rtype and pattern and category):
                    continue
                conn.execute(
                    "INSERT INTO rules (type, pattern, category, enabled, created_at) VALUES (?, ?, ?, ?, ?)",
                    (rtype, pattern, category, enabled, _utcnow_iso()),
                )
            conn.commit()
        except Exception:
            conn.rollback()

    def create_run(self, dry_run: bool, limit_count: int, days_window: int) -> str:
        run_id = str(uuid.uuid4())
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO runs (id, started_at, status, dry_run, limit_count, days_window) VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, _utcnow_iso(), "running", int(dry_run), limit_count, days_window),
            )
            conn.commit()
        finally:
            conn.close()
        return run_id

    def finish_run(self, run_id: str, status: str, total_count: int, moved_count: int, errors_count: int) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE runs SET finished_at=?, status=?, total_count=?, moved_count=?, errors_count=? WHERE id=?",
                (_utcnow_iso(), status, total_count, moved_count, errors_count, run_id),
            )
            conn.commit()
        finally:
            conn.close()

    def save_message(self, run_id: str, message: Dict[str, Any]) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO messages (
                    run_id, entry_id, subject, sender_email, sender_name, received_time,
                    category, explain_json, body_excerpt, body_hash, attachments_json, outcome, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    message.get("entry_id"),
                    message.get("subject"),
                    message.get("sender_email"),
                    message.get("sender_name"),
                    message.get("received_time"),
                    message.get("category"),
                    json.dumps(message.get("explain"), ensure_ascii=False),
                    message.get("body_excerpt"),
                    message.get("body_hash"),
                    json.dumps(message.get("attachments") or [], ensure_ascii=False),
                    message.get("outcome"),
                    _utcnow_iso(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_logs(
        self, run_id: Optional[str] = None, level: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            query = "SELECT ts, level, run_id, event, details_json FROM logs WHERE 1=1"
            params: List[Any] = []
            if run_id:
                query += " AND run_id = ?"
                params.append(run_id)
            if level:
                query += " AND level = ?"
                params.append(level)
            query += " ORDER BY id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                results.append(
                    {
                        "ts": row["ts"],
                        "level": row["level"],
                        "run_id": row["run_id"],
                        "event": row["event"],
                        "details": json.loads(row["details_json"]) if row["details_json"] else None,
                    }
                )
            return results
        finally:
            conn.close()

    def append_log(self, level: str, event: str, run_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        payload = {
            "ts": _utcnow_iso(),
            "level": level,
            "run_id": run_id,
            "event": event,
            "details": details or {},
        }
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO logs (ts, level, run_id, event, details_json) VALUES (?, ?, ?, ?, ?)",
                (payload["ts"], level, run_id, event, json.dumps(payload["details"], ensure_ascii=False)),
            )
            conn.commit()
        finally:
            conn.close()
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def save_consignes(self, text: str) -> None:
        conn = self._connect()
        try:
            conn.execute("INSERT INTO consignes (text, created_at) VALUES (?, ?)", (text, _utcnow_iso()))
            conn.commit()
        finally:
            conn.close()

    def get_latest_consignes(self) -> str:
        conn = self._connect()
        try:
            row = conn.execute("SELECT text FROM consignes ORDER BY id DESC LIMIT 1").fetchone()
            return row["text"] if row else ""
        finally:
            conn.close()

    def list_consignes(self, limit: int = 20) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, text, created_at FROM consignes ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [{"id": r["id"], "text": r["text"], "created_at": r["created_at"]} for r in rows]
        finally:
            conn.close()

    def get_rules(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM rules WHERE enabled = 1 ORDER BY id ASC").fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def add_rule(self, rule_type: str, pattern: str, category: str, enabled: bool = True) -> int:
        conn = self._connect()
        try:
            cur = conn.execute(
                "INSERT INTO rules (type, pattern, category, enabled, created_at) VALUES (?, ?, ?, ?, ?)",
                (rule_type, pattern, category, int(enabled), _utcnow_iso()),
            )
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()

    def get_genial_config(self) -> Dict[str, Any]:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM genial_config WHERE id = 1").fetchone()
            if not row:
                return {}
            return dict(row)
        finally:
            conn.close()

    def save_genial_config(self, config: Dict[str, Any]) -> None:
        now = _utcnow_iso()
        conn = self._connect()
        try:
            existing = conn.execute("SELECT id FROM genial_config WHERE id = 1").fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE genial_config
                    SET enabled=?, base_url=?, path=?, method=?, allowlist_hosts_ports=?, headers_json=?,
                        timeout_seconds=?, retries=?, request_template=?, response_mapping_json=?, updated_at=?
                    WHERE id=1
                    """,
                    (
                        int(config.get("enabled", 0)),
                        config.get("base_url"),
                        config.get("path"),
                        config.get("method"),
                        config.get("allowlist_hosts_ports"),
                        config.get("headers_json"),
                        config.get("timeout_seconds"),
                        config.get("retries"),
                        config.get("request_template"),
                        config.get("response_mapping_json"),
                        now,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO genial_config (
                        id, enabled, base_url, path, method, allowlist_hosts_ports, headers_json,
                        timeout_seconds, retries, request_template, response_mapping_json, created_at, updated_at
                    ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(config.get("enabled", 0)),
                        config.get("base_url"),
                        config.get("path"),
                        config.get("method"),
                        config.get("allowlist_hosts_ports"),
                        config.get("headers_json"),
                        config.get("timeout_seconds"),
                        config.get("retries"),
                        config.get("request_template"),
                        config.get("response_mapping_json"),
                        now,
                        now,
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def save_summary(self, run_id: str, date: str, content_md: str) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO summaries (run_id, date, content_md, created_at) VALUES (?, ?, ?, ?)",
                (run_id, date, content_md, _utcnow_iso()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_latest_summary(self) -> Optional[Dict[str, Any]]:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT run_id, date, content_md, created_at FROM summaries ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            return dict(row)
        finally:
            conn.close()

    def get_latest_run_id(self) -> Optional[str]:
        conn = self._connect()
        try:
            row = conn.execute("SELECT id FROM runs ORDER BY started_at DESC LIMIT 1").fetchone()
            return row["id"] if row else None
        finally:
            conn.close()

    def get_messages_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT subject, sender_email, sender_name, received_time, category, body_excerpt, explain_json, attachments_json
                FROM messages WHERE run_id = ? ORDER BY id ASC
                """,
                (run_id,),
            ).fetchall()
            results = []
            for row in rows:
                results.append(
                    {
                        "subject": row["subject"],
                        "sender_email": row["sender_email"],
                        "sender_name": row["sender_name"],
                        "received_time": row["received_time"],
                        "category": row["category"],
                        "body_excerpt": row["body_excerpt"],
                        "attachments": json.loads(row["attachments_json"]) if row["attachments_json"] else [],
                        "explain": json.loads(row["explain_json"]) if row["explain_json"] else None,
                    }
                )
            return results
        finally:
            conn.close()

    def acquire_lock(self, name: str, ttl_seconds: int = 900) -> Optional[str]:
        owner_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT owner_id, expires_at FROM locks WHERE name = ?", (name,)).fetchone()
            if row:
                existing_expires = datetime.fromisoformat(row["expires_at"])
                if existing_expires < now:
                    conn.execute(
                        "UPDATE locks SET owner_id=?, expires_at=? WHERE name=?",
                        (owner_id, expires_at.isoformat(), name),
                    )
                    conn.commit()
                    return owner_id
                conn.rollback()
                return None
            conn.execute(
                "INSERT INTO locks (name, owner_id, expires_at) VALUES (?, ?, ?)",
                (name, owner_id, expires_at.isoformat()),
            )
            conn.commit()
            return owner_id
        finally:
            conn.close()

    def release_lock(self, name: str, owner_id: str) -> None:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM locks WHERE name = ? AND owner_id = ?", (name, owner_id))
            conn.commit()
        finally:
            conn.close()
