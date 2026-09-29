from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from .models import AccountsFile, ProductionConfig

TERMS_WARNING = (
    "AVISO: Usar várias contas gratuitas pode violar os termos de uso da ferramenta; "
    "o risco é do usuário."
)


def read_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_production(root: Path) -> ProductionConfig:
    return ProductionConfig.model_validate(read_yaml(root / "config" / "production.yaml"))


def load_accounts(root: Path) -> AccountsFile:
    return AccountsFile.model_validate(read_yaml(root / "config" / "accounts.yaml"))


def show_first_run_warning(root: Path) -> bool:
    """Print and persist the terms warning once per local project."""
    state_path = root / ".studio_state.json"
    state: dict[str, object] = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            state = {}
    if state.get("terms_warning_shown") is True:
        return False
    state["terms_warning_shown"] = True
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(TERMS_WARNING)
    return True


def set_active_profile(root: Path, profile_name: str) -> Path:
    path = root / "config" / "production.yaml"
    production = load_production(root)
    production.profile(profile_name)
    content = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"(?m)^(active_profile:\s*)\S+(\s*(?:#.*)?)$",
        lambda match: f"{match.group(1)}{profile_name}{match.group(2)}",
        content,
        count=1,
    )
    if count == 0:
        updated = f"active_profile: {profile_name}\n{content}"
    path.write_text(updated, encoding="utf-8")
    return path


def load_goals(root: Path) -> dict | None:
    path = root / "config" / "goals.yaml"
    if not path.exists():
        return None
    return read_yaml(path)
