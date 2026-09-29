from pathlib import Path

from typer.testing import CliRunner

from studio.cli import app

ROOT = Path(__file__).parents[1]
RUNNER = CliRunner()


def test_lint_command_prints_rich_table_and_succeeds_with_warnings() -> None:
    result = RUNNER.invoke(
        app,
        ["lint", "revenge_republic", "ep01"],
        env={"PWD": str(ROOT)},
    )
    assert result.exit_code == 0
    assert "Pacing lint" in result.stdout
    assert "P01" in result.stdout


def test_brief_new_and_check_commands_report_empty_sections(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "series" / "demo").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    created = RUNNER.invoke(app, ["brief", "new", "demo"])
    assert created.exit_code == 0
    checked = RUNNER.invoke(app, ["brief", "check", "demo"])
    assert checked.exit_code == 1
    assert "Premissa" in checked.stdout


def test_bible_check_accepts_paused_fixture() -> None:
    result = RUNNER.invoke(
        app,
        ["bible", "check", "revenge_republic"],
        env={"PWD": str(ROOT)},
    )
    assert result.exit_code == 0
    assert "Verificação da bíblia" in result.stdout
    assert "OK: bible revenge_republic" in result.stdout


def test_validate_downgrades_bible_errors_for_planning(tmp_path: Path, monkeypatch) -> None:
    import shutil

    for directory in ("config", "styles"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    shutil.copytree(ROOT / "series" / "revenge_republic", tmp_path / "series" / "demo")
    series_path = tmp_path / "series" / "demo" / "series.yaml"
    series_path.write_text(
        series_path.read_text(encoding="utf-8").replace(
            "id: revenge_republic", "id: demo", 1
        ).replace("status: paused", "status: planning", 1),
        encoding="utf-8",
    )
    (tmp_path / "series" / "demo" / "bible.md").write_text("# Bíblia\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = RUNNER.invoke(app, ["validate", "demo"])
    assert result.exit_code == 0
    assert "WARNING: Bíblia:" in result.stdout


def test_validate_blocks_bible_errors_in_production(tmp_path: Path, monkeypatch) -> None:
    import shutil

    for directory in ("config", "styles"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    shutil.copytree(ROOT / "series" / "revenge_republic", tmp_path / "series" / "demo")
    series_path = tmp_path / "series" / "demo" / "series.yaml"
    series_path.write_text(
        series_path.read_text(encoding="utf-8").replace(
            "id: revenge_republic", "id: demo", 1
        ).replace("status: paused", "status: in_production", 1),
        encoding="utf-8",
    )
    (tmp_path / "series" / "demo" / "bible.md").write_text("# Bíblia\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = RUNNER.invoke(app, ["validate", "demo"])
    assert result.exit_code == 1
    assert "ERROR: Bíblia:" in result.stdout


def test_profile_show_and_set_commands(tmp_path: Path, monkeypatch) -> None:
    import shutil

    for directory in ("config", "series", "styles"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    production_path = tmp_path / "config" / "production.yaml"
    production_path.write_text(
        production_path.read_text(encoding="utf-8").replace(
            "active_profile: growth", "active_profile: growth  # selected by the producer"
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    shown = RUNNER.invoke(app, ["profile", "show"])
    assert shown.exit_code == 0
    assert "Perfil ativo: growth" in shown.stdout
    assert "1080p" in shown.stdout
    changed = RUNNER.invoke(app, ["profile", "set", "monetize"])
    assert changed.exit_code == 0
    assert "Requisitos de qualificação" in changed.stdout
    assert "goals.yaml ainda não existe" in changed.stdout
    assert "active_profile: monetize  # selected by the producer" in production_path.read_text(
        encoding="utf-8"
    )


def test_validate_prints_profile_and_stale_cost_warning() -> None:
    result = RUNNER.invoke(
        app,
        ["validate", "revenge_republic", "ep01"],
        env={"PWD": str(ROOT)},
    )
    assert result.exit_code == 1
    assert "Perfil ativo: growth" in result.stdout
    assert "Conferir custos na interface do Flow: eles mudam" in result.stdout
