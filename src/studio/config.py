from __future__ import annotations

import re
from pathlib import Path

import yaml

from .models import AccountsFile, ProductionConfig


def read_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_production(root: Path) -> ProductionConfig:
    return ProductionConfig.model_validate(read_yaml(root / "config" / "production.yaml"))


def load_accounts(root: Path) -> AccountsFile:
    return AccountsFile.model_validate(read_yaml(root / "config" / "accounts.yaml"))


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
