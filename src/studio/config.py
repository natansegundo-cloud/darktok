from __future__ import annotations

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
