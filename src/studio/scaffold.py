from __future__ import annotations

import shutil
from pathlib import Path

import yaml

TEMPLATE_DIRS = ("series", "episode", "prompts")


def _copy_if_missing(source: Path, target: Path) -> None:
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def init_project(root: Path) -> list[Path]:
    created: list[Path] = []
    for directory in (
        root / "config",
        root / "docs",
        root / "styles",
        root / "templates",
        root / "series",
        root / "src" / "studio",
        root / "tests",
        root / "output",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    (root / "output" / ".gitkeep").touch(exist_ok=True)
    return created


def new_series(root: Path, series_id: str) -> Path:
    series_dir = root / "series" / series_id
    if series_dir.exists():
        raise FileExistsError(f"Series already exists: {series_id}")
    series_dir.mkdir(parents=True)
    for name in ("series.yaml", "characters.yaml", "locations.yaml", "bible.md"):
        source = root / "templates" / "series" / name
        target = series_dir / name
        _copy_if_missing(source, target)
    data = yaml.safe_load((series_dir / "series.yaml").read_text(encoding="utf-8"))
    data["id"] = series_id
    (series_dir / "series.yaml").write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    (series_dir / "references").mkdir()
    (series_dir / "shared_assets" / "anchors").mkdir(parents=True)
    (series_dir / "shared_assets" / "characters").mkdir(parents=True)
    (series_dir / "episodes").mkdir()
    return series_dir


def new_episode(root: Path, series_id: str, number: int) -> Path:
    episode_id = f"ep{number:02d}"
    episode_dir = root / "series" / series_id / "episodes" / episode_id
    if episode_dir.exists():
        raise FileExistsError(f"Episode already exists: {episode_id}")
    episode_dir.mkdir(parents=True)
    for name in ("episode.yaml", "script.md", "shots.yaml"):
        _copy_if_missing(root / "templates" / "episode" / name, episode_dir / name)
    data = yaml.safe_load((episode_dir / "episode.yaml").read_text(encoding="utf-8"))
    data["id"] = episode_id
    data["number"] = number
    (episode_dir / "episode.yaml").write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    (episode_dir / "prompts").mkdir()
    for directory in ("images", "videos"):
        (episode_dir / "assets" / directory).mkdir(parents=True)
    (episode_dir / "edit").mkdir()
    (episode_dir / "export").mkdir()
    return episode_dir


def new_style(root: Path, style_id: str) -> Path:
    target = root / "styles" / f"{style_id}.yaml"
    if target.exists():
        raise FileExistsError(f"Style already exists: {style_id}")
    source = root / "styles" / "_template.yaml"
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    data["id"] = style_id
    data["name"] = style_id.replace("_", " ").title()
    target.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return target
