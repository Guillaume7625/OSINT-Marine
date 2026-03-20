import queue
from datetime import datetime
from typing import Any, Dict, Optional

from flask import Flask, jsonify, redirect, render_template, request, url_for

from .genial_client import GenialClient
from .outlook_client import OutlookClient
from .run_job import run_job
from .security import load_settings, token_required
from .storage import Storage
from .summarizer import generate_summary


class JobQueue:
    def __init__(self) -> None:
        self._queue: "queue.Queue" = queue.Queue()
        self._thread = None

    def start(self) -> None:
        if self._thread:
            return
        import threading

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while True:
            task = self._queue.get()
            if task is None:
                break
            func, args, kwargs, event, container = task
            try:
                container["result"] = func(*args, **kwargs)
            except Exception as exc:
                container["error"] = exc
            finally:
                event.set()

    def submit(self, func, *args, **kwargs):
        import threading

        event = threading.Event()
        container: Dict[str, Any] = {"result": None, "error": None}
        self._queue.put((func, args, kwargs, event, container))
        event.wait()
        if container["error"]:
            raise container["error"]
        return container["result"]


def create_app() -> Flask:
    app = Flask(__name__)
    storage = Storage()
    settings = load_settings()
    job_queue = JobQueue()
    job_queue.start()

    def _get_token() -> str:
        return request.args.get("token") or request.headers.get("X-Auth-Token") or ""

    @app.route("/")
    def index():
        return redirect(url_for("consignes"))

    @app.route("/consignes", methods=["GET", "POST"])
    def consignes():
        if request.method == "POST":
            text = request.form.get("text") or ""
            storage.save_consignes(text)
            return redirect(url_for("consignes"))
        latest = storage.get_latest_consignes()
        history = storage.list_consignes(limit=10)
        return render_template("consignes.html", latest=latest, history=history)

    @app.route("/trier", methods=["GET", "POST"])
    def trier():
        if request.method == "GET":
            return render_template("trier.html")
        dry_run = (request.form.get("dry_run") or "true").lower() in ("1", "true", "yes")
        limit = int(request.form.get("limit") or 50)
        days_window = int(request.form.get("days_window") or 7)
        if not dry_run and not token_required(settings, _get_token()):
            return "Token requis", 403
        result = job_queue.submit(run_job, limit=limit, days_window=days_window, dry_run=dry_run)
        return jsonify(result)

    @app.route("/resume", methods=["GET"])
    def resume():
        run_id = storage.get_latest_run_id()
        if not run_id:
            return render_template("resume.html", content_md="Aucun traitement disponible.", saved_path=None)
        messages = storage.get_messages_for_run(run_id)
        content_md, _ = generate_summary(messages)
        today = datetime.now().strftime("%Y-%m-%d")
        path = Storage().db_path.parent / f"{today}.md"
        path.write_text(content_md, encoding="utf-8")
        storage.save_summary(run_id, today, content_md)
        storage.append_log("INFO", "summary_generated", run_id, {"path": str(path)})
        if request.args.get("draft") == "1":
            folder_name = request.args.get("folder") or None
            OutlookClient().create_summary_draft("Résumé Cycle", content_md, folder_name=folder_name)
        return render_template("resume.html", content_md=content_md, saved_path=str(path))

    @app.route("/logs", methods=["GET"])
    def logs():
        if not token_required(settings, _get_token()):
            return "Token requis", 403
        run_id = request.args.get("run_id")
        level = request.args.get("level")
        limit = int(request.args.get("limit") or 100)
        offset = int(request.args.get("offset") or 0)
        entries = storage.list_logs(run_id=run_id, level=level, limit=limit, offset=offset)
        return render_template("logs.html", entries=entries)

    @app.route("/genial", methods=["GET", "POST"])
    def genial():
        if not token_required(settings, _get_token()):
            return "Token requis", 403
        config = storage.get_genial_config() or {}
        test_result: Optional[Dict[str, Any]] = None
        if request.method == "POST":
            action = request.form.get("action") or "save"
            config = {
                "enabled": 1 if request.form.get("enabled") else 0,
                "base_url": request.form.get("base_url") or "",
                "path": request.form.get("path") or "",
                "method": request.form.get("method") or "POST",
                "allowlist_hosts_ports": request.form.get("allowlist_hosts_ports") or "[]",
                "headers_json": request.form.get("headers_json") or "{}",
                "timeout_seconds": int(request.form.get("timeout_seconds") or 10),
                "retries": int(request.form.get("retries") or 1),
                "request_template": request.form.get("request_template") or "{}",
                "response_mapping_json": request.form.get("response_mapping_json") or "{}",
            }
            storage.save_genial_config(config)
            if action == "test":
                client = GenialClient(storage)
                payload = {
                    "instructions_utilisateur": storage.get_latest_consignes(),
                    "from": "alice@example.com",
                    "to_cc": "bob@example.com",
                    "subject": "Test de configuration",
                    "received_time_iso": datetime.now().isoformat(),
                    "body_excerpt": "Merci de valider le budget avant EOD.",
                }
                result = client.test_request(payload)
                test_result = {
                    "category": result.category,
                    "confidence": result.confidence,
                    "reasons": result.reasons,
                    "error": result.error,
                    "status_code": result.status_code,
                    "raw_response": (result.raw_response or "")[:2000],
                    "parsed_json": result.parsed_json,
                    "mapped": result.mapped,
                }
        return render_template("genial.html", config=config, test_result=test_result)

    return app


def main() -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=False)


if __name__ == "__main__":
    main()
