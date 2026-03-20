import os
from pathlib import Path
from typing import Any, Dict

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"


def load_settings() -> Dict[str, Any]:
    settings: Dict[str, Any] = {}
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            settings = yaml.safe_load(handle) or {}
    ui_settings = settings.setdefault("ui", {})
    env_require = os.getenv("CYCLE_UI_REQUIRE_TOKEN")
    if env_require is not None:
        ui_settings["require_token"] = env_require.lower() in ("1", "true", "yes")
    env_token = os.getenv("CYCLE_UI_TOKEN")
    if env_token:
        ui_settings["token"] = env_token
    return settings


def token_required(settings: Dict[str, Any], provided: str) -> bool:
    ui = settings.get("ui", {})
    require = bool(ui.get("require_token"))
    if not require:
        return True
    expected = ui.get("token")
    if not expected:
        return False
    return provided == expected
