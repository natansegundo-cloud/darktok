from pathlib import Path

from studio.scaffold import new_episode, new_series, new_style


def test_scaffold_creates_series_episode_and_style(tmp_path: Path) -> None:
    root = tmp_path
    (root / "templates" / "series").mkdir(parents=True)
    (root / "templates" / "episode").mkdir(parents=True)
    (root / "styles").mkdir()
    (root / "templates" / "series" / "series.yaml").write_text("id: series_id\n", encoding="utf-8")
    for name, content in {
        "characters.yaml": "characters: []\n",
        "locations.yaml": "locations: []\n",
        "bible.md": "# Bible\n",
    }.items():
        (root / "templates" / "series" / name).write_text(content, encoding="utf-8")
    (root / "templates" / "episode" / "episode.yaml").write_text(
        "id: ep01\nnumber: 1\n", encoding="utf-8"
    )
    for name in ("script.md", "shots.yaml"):
        (root / "templates" / "episode" / name).write_text("", encoding="utf-8")
    (root / "styles" / "_template.yaml").write_text("id: new_style\n", encoding="utf-8")

    series_dir = new_series(root, "demo")
    episode_dir = new_episode(root, "demo", 1)
    style_path = new_style(root, "comic")
    assert series_dir.name == "demo"
    assert episode_dir.name == "ep01"
    assert style_path.name == "comic.yaml"
