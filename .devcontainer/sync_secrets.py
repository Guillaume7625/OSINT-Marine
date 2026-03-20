from __future__ import annotations

import os
from pathlib import Path

PLACEHOLDERS = {
    "",
    "changeme",
    "placeholder",
    "replace_me",
    "test",
    "your_anthropic_api_key",
    "your_key_here",
}


def upsert_env_value(path: Path, key: str, value: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    prefix = f"{key}="
    updated = False
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            lines[idx] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if key.lower() in PLACEHOLDERS:
        print("ANTHROPIC_API_KEY not provided via Codespaces secret; keeping placeholder env values.")
        return 0

    targets = [Path("infra/.env"), Path(".env")]
    for target in targets:
        if target.exists():
            upsert_env_value(path=target, key="ANTHROPIC_API_KEY", value=key)
            print(f"Updated {target} with ANTHROPIC_API_KEY from environment.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
