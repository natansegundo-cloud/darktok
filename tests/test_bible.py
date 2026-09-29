from pathlib import Path

from studio.bible import BIBLE_SECTIONS, check_bible, has_bible_errors

ROOT = Path(__file__).parents[1]
GRADE_HEADING = BIBLE_SECTIONS[6]


def _write_project(
    root: Path,
    *,
    planned: int = 1,
    rows: list[tuple[str, str, str, str]] | None = None,
    status: str = "planning",
    overrides: dict[str, str] | None = None,
) -> Path:
    series_dir = root / "series" / "demo"
    series_dir.mkdir(parents=True)
    (series_dir / "series.yaml").write_text(
        f"id: demo\ntitle: Demo\nstyle: demo\nepisodes_planned: {planned}\nstatus: {status}\n",
        encoding="utf-8",
    )
    episode_rows = rows or [
        ("1", "Ação já começou", "A prova muda de mão", "A resposta fica aberta")
    ]
    lines = ["# Bíblia da série", ""]
    overrides = overrides or {}
    for heading in BIBLE_SECTIONS:
        lines.extend([f"## {heading}", ""])
        if heading == GRADE_HEADING:
            content = [
                "| nº | abertura já no meio da ação | virada | cliffhanger |",
                "| --- | --- | --- | --- |",
            ]
            content.extend(f"| {' | '.join(row)} |" for row in episode_rows)
            lines.extend(content)
        else:
            lines.append(
                overrides.get(
                    heading,
                    "Esta seção descreve uma decisão concreta da série, com contexto suficiente "
                    "para orientar autoria e verificação.",
                )
            )
        lines.append("")
    (series_dir / "bible.md").write_text("\n".join(lines), encoding="utf-8")
    return series_dir


def test_valid_bible_passes(tmp_path: Path) -> None:
    _write_project(tmp_path)
    report = check_bible(tmp_path, "demo")
    assert report.issues == ()


def test_missing_required_heading_fails(tmp_path: Path) -> None:
    series_dir = _write_project(tmp_path)
    text = (series_dir / "bible.md").read_text(encoding="utf-8")
    text = text.replace(f"## {BIBLE_SECTIONS[0]}\n\n", "")
    (series_dir / "bible.md").write_text(text, encoding="utf-8")
    report = check_bible(tmp_path, "demo")
    assert has_bible_errors(report)
    assert any("Seção obrigatória ausente" in issue.message for issue in report.issues)


def test_short_section_fails(tmp_path: Path) -> None:
    _write_project(tmp_path, overrides={BIBLE_SECTIONS[0]: "curto"})
    report = check_bible(tmp_path, "demo")
    assert any("mínimo: 80" in issue.message for issue in report.issues)


def test_placeholder_fails(tmp_path: Path) -> None:
    _write_project(tmp_path, overrides={BIBLE_SECTIONS[1]: "TODO " + "conteúdo " * 20})
    report = check_bible(tmp_path, "demo")
    assert any("placeholder 'TODO'" in issue.message for issue in report.issues)


def test_episode_grade_requires_enough_rows(tmp_path: Path) -> None:
    _write_project(tmp_path, planned=2)
    report = check_bible(tmp_path, "demo")
    assert any("Grade de episódios tem 1 linhas" in issue.message for issue in report.issues)


def test_episode_grade_requires_cliffhanger(tmp_path: Path) -> None:
    _write_project(tmp_path, rows=[("1", "Ação", "Virada", "")])
    report = check_bible(tmp_path, "demo")
    assert any("sem cliffhanger" in issue.message for issue in report.issues)


def test_repeated_cliffhanger_is_warning(tmp_path: Path) -> None:
    _write_project(
        tmp_path,
        planned=2,
        rows=[
            ("1", "Ação um", "Virada um", "A mesma pergunta fica aberta"),
            ("2", "Ação dois", "Virada dois", "a mesma pergunta fica aberta"),
        ],
    )
    report = check_bible(tmp_path, "demo")
    assert not has_bible_errors(report)
    assert any(issue.level == "warning" for issue in report.issues)


def test_paused_fixture_bible_is_accepted() -> None:
    report = check_bible(ROOT, "revenge_republic")
    assert report.status == "paused"
    assert not has_bible_errors(report)
    assert 'notes: "Fixture de teste. Não publicar."' in (
        ROOT / "series" / "revenge_republic" / "series.yaml"
    ).read_text(encoding="utf-8")
