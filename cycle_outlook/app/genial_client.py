import json
import os
import random
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from jinja2 import Template

from .storage import Storage

ALLOWED_CATEGORIES = {"CRISES", "DECISIONS", "A_LIRE"}


@dataclass
class GenialResult:
    category: Optional[str]
    confidence: Optional[float]
    reasons: List[str]
    error: Optional[str]
    raw_response: Optional[str]
    mapped: Optional[Dict[str, Any]]
    status_code: Optional[int] = None
    parsed_json: Optional[Any] = None


class GenialClient:
    def __init__(self, storage: Optional[Storage] = None) -> None:
        self.storage = storage or Storage()

    def _parse_json(self, raw: Optional[str]) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def _expand_env(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        pattern = re.compile(r"\$\{([A-Z0-9_]+)\}")
        expanded: Dict[str, Any] = {}
        for key, value in headers.items():
            if isinstance(value, str):
                def repl(match):
                    return os.getenv(match.group(1), "")
                expanded[key] = pattern.sub(repl, value)
            else:
                expanded[key] = value
        return expanded

    def _load_config(self) -> Dict[str, Any]:
        config = self.storage.get_genial_config() or {}
        allowlist = self._parse_json(config.get("allowlist_hosts_ports")) or []
        headers = self._parse_json(config.get("headers_json")) or {}
        mapping = self._parse_json(config.get("response_mapping_json")) or {}
        headers = self._expand_env(headers)
        return {
            "enabled": bool(config.get("enabled")),
            "base_url": config.get("base_url") or "",
            "path": config.get("path") or "",
            "method": (config.get("method") or "POST").upper(),
            "allowlist": allowlist,
            "headers": headers,
            "timeout_seconds": int(config.get("timeout_seconds") or 10),
            "retries": int(config.get("retries") or 1),
            "request_template": config.get("request_template") or "",
            "response_mapping": mapping,
        }

    def _is_allowed(self, url: str, allowlist: List[str]) -> bool:
        if not allowlist:
            return False
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return False
        port = parsed.port
        if not port:
            port = 443 if parsed.scheme == "https" else 80
        host_port = f"{host}:{port}"
        return host_port in allowlist

    def _get_by_path(self, data: Any, path: Optional[str]) -> Any:
        if data is None or not path:
            return None
        cur = data
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur

    def _map_response(self, data: Any, mapping: Dict[str, Any]) -> Tuple[Optional[str], Optional[float], List[str], Dict[str, Any]]:
        defaults = mapping.get("defaults", {}) if isinstance(mapping, dict) else {}
        category = self._get_by_path(data, mapping.get("category_path")) if isinstance(mapping, dict) else None
        confidence = self._get_by_path(data, mapping.get("confidence_path")) if isinstance(mapping, dict) else None
        reasons = self._get_by_path(data, mapping.get("reasons_path")) if isinstance(mapping, dict) else None

        if category is None:
            category = defaults.get("category")
        if confidence is None:
            confidence = defaults.get("confidence")
        if reasons is None:
            reasons = defaults.get("reasons") or []
        if isinstance(reasons, str):
            reasons = [reasons]
        if category and category not in ALLOWED_CATEGORIES:
            category = None
        mapped = {
            "category": category,
            "confidence": confidence,
            "reasons": reasons,
        }
        return category, confidence, reasons, mapped

    def is_enabled(self) -> bool:
        config = self._load_config()
        return bool(config.get("enabled"))

    def classify(self, payload: Dict[str, Any]) -> GenialResult:
        config = self._load_config()
        if not config.get("enabled"):
            return GenialResult(None, None, [], "GENIAL disabled", None, None)

        url = urljoin(config["base_url"], config["path"])
        if not self._is_allowed(url, config["allowlist"]):
            self.storage.append_log("WARNING", "genial_blocked", None, {"url": url})
            return GenialResult(None, None, [], "Host/port non autorise", None, None)

        template = Template(config["request_template"] or "{}")
        rendered = template.render(**payload)
        json_payload = None
        try:
            json_payload = json.loads(rendered)
        except json.JSONDecodeError:
            json_payload = None

        session = requests.Session()
        session.trust_env = False
        method = config["method"]
        timeout = config["timeout_seconds"]
        retries = max(config["retries"], 1)
        headers = config["headers"]

        last_error = None
        raw_text = None
        for attempt in range(retries):
            try:
                if method == "GET":
                    response = session.request(
                        method,
                        url,
                        headers=headers,
                        params=json_payload if isinstance(json_payload, dict) else None,
                        timeout=timeout,
                        allow_redirects=False,
                    )
                else:
                    if json_payload is not None:
                        response = session.request(
                            method,
                            url,
                            headers=headers,
                            json=json_payload,
                            timeout=timeout,
                            allow_redirects=False,
                        )
                    else:
                        response = session.request(
                            method,
                            url,
                            headers=headers,
                            data=rendered.encode("utf-8"),
                            timeout=timeout,
                            allow_redirects=False,
                        )
                raw_text = response.text
                if response.is_redirect or 300 <= response.status_code < 400:
                    self.storage.append_log(
                        "WARNING", "genial_redirect_blocked", None, {"status_code": response.status_code}
                    )
                    return GenialResult(None, None, [], "Redirection interdite", raw_text, None, response.status_code, None)
                data = self._parse_json(raw_text)
                if data is None:
                    self.storage.append_log("WARNING", "genial_non_json", None, {"status_code": response.status_code})
                    return GenialResult(None, None, [], "Reponse non JSON", raw_text, None, response.status_code, None)
                category, confidence, reasons, mapped = self._map_response(data, config["response_mapping"])
                if not category:
                    self.storage.append_log("WARNING", "genial_invalid_category", None, {"mapped": mapped})
                    return GenialResult(None, None, [], "Categorie invalide", raw_text, mapped, response.status_code, data)
                return GenialResult(category, confidence, reasons, None, raw_text, mapped, response.status_code, data)
            except requests.RequestException as exc:
                last_error = str(exc)
                if attempt < retries - 1:
                    delay = 0.5 * (2**attempt) + random.uniform(0, 0.25)
                    time.sleep(delay)
                continue
        self.storage.append_log("WARNING", "genial_request_failed", None, {"error": last_error})
        return GenialResult(None, None, [], last_error or "Erreur inconnue", raw_text, None)

    def test_request(self, payload: Dict[str, Any]) -> GenialResult:
        return self.classify(payload)
