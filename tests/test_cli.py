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
