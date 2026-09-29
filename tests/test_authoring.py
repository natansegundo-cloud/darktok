from pathlib import Path

import pytest

from studio.authoring import BRIEF_SECTIONS, check_brief, create_brief, scaffold_episode


def _copy_templates(root: Path) -> None:
    (root / "templates" / "episode").mkdir(parents=True)
    (root / "templates" / "episode" / "episode.yaml").write_text(
        "id: ep01\nnumber: 1\n", encoding="utf-8"
    )
    (root / "templates" / "episode" / "script.md").write_text("# Roteiro\n", encoding="utf-8")
    (root / "templates" / "episode" / "shots.yaml").write_text(
        "shots: []\nvoice_over_pt: []\nbeat_pt: ''\n", encoding="utf-8"
    )


def test_brief_new_and_check_report_empty_sections(tmp_path: Path) -> None:
    series_dir = tmp_path / "series" / "demo"
    series_dir.mkdir(parents=True)
    path = create_brief(tmp_path, "demo")
    assert path.exists()
    missing = check_brief(tmp_path, "demo")
    assert missing == [title for title, _ in BRIEF_SECTIONS]


def test_brief_check_accepts_filled_sections(tmp_path: Path) -> None:
    series_dir = tmp_path / "series" / "demo"
    series_dir.mkdir(parents=True)
    create_brief(tmp_path, "demo")
    path = series_dir / "brief_pt.md"
    path.write_text(
        "\n".join([f"## {title}\nconteúdo" for title, _ in BRIEF_SECTIONS]), encoding="utf-8"
    )
    assert check_brief(tmp_path, "demo") == []


def test_scaffold_requires_episode_format(tmp_path: Path) -> None:
    _copy_templates(tmp_path)
    (tmp_path / "series" / "demo").mkdir(parents=True)
    with pytest.raises(ValueError):
        scaffold_episode(tmp_path, "demo", "1")
