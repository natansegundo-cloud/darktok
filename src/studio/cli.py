from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .authoring import check_brief, create_brief, scaffold_episode
from .board import next_row, write_board
from .config import load_production
from .loader import ProjectLoader
from .pacing import lint_bundle, pacing_table
from .prompts import validate_bundle, write_prompts
from .scaffold import init_project, new_episode, new_series, new_style

app = typer.Typer(help="Offline production studio for vertical AI dramas.", no_args_is_help=True)
series_app = typer.Typer(help="Manage series.", no_args_is_help=True)
style_app = typer.Typer(help="Manage style presets.", no_args_is_help=True)
brief_app = typer.Typer(help="Manage Portuguese authoring briefs.", no_args_is_help=True)
app.add_typer(series_app, name="series")
app.add_typer(style_app, name="style")
app.add_typer(brief_app, name="brief")


def _root() -> Path:
    return Path.cwd()


@app.command()
def init() -> None:
    """Create the base project directories."""
    created = init_project(_root())
    typer.echo(f"Project ready at {_root()}")
    if created:
        typer.echo(f"Created {len(created)} paths")
    typer.echo("Warning: using multiple free accounts may violate the generation tool's terms.")
    typer.echo("Studio never logs in to accounts or automates the Flow.")


@series_app.command("new")
def series_new(series_id: str) -> None:
    """Create a series from the templates."""
    try:
        path = new_series(_root(), series_id)
    except FileExistsError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Created series: {path}")


@series_app.command("list")
def series_list() -> None:
    """List series and their status."""
    root = _root() / "series"
    if not root.exists():
        typer.echo("No series found.")
        return
    found = False
    for path in sorted(item for item in root.iterdir() if item.is_dir()):
        found = True
        loader = ProjectLoader(_root())
        try:
            series = loader.load_series(path.name)
            typer.echo(f"{series.id}\t{series.status}\t{series.title}")
        except Exception as exc:
            typer.echo(f"{path.name}\tINVALID\t{exc}")
    if not found:
        typer.echo("No series found.")


@style_app.command("new")
def style_new(style_id: str) -> None:
    """Create a style preset from the template."""
    try:
        path = new_style(_root(), style_id)
    except FileExistsError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Created style: {path}")


@style_app.command("list")
def style_list() -> None:
    """List style presets."""
    directory = _root() / "styles"
    for path in sorted(directory.glob("*.yaml")):
        if path.name != "_template.yaml":
            typer.echo(path.stem)


episode_app = typer.Typer(help="Manage episodes.", no_args_is_help=True)
app.add_typer(episode_app, name="episode")


@episode_app.command("new")
def episode_new(series_id: str, number: int) -> None:
    """Create an episode from the templates."""
    try:
        path = new_episode(_root(), series_id, number)
    except FileExistsError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Created episode: {path}")


@brief_app.command("new")
def brief_new(series_id: str) -> None:
    """Create a Portuguese authoring brief for a series."""
    try:
        path = create_brief(_root(), series_id)
    except (FileExistsError, FileNotFoundError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Created brief: {path}")


@brief_app.command("check")
def brief_check(series_id: str) -> None:
    """Report empty sections in a Portuguese authoring brief."""
    try:
        missing = check_brief(_root(), series_id)
    except FileNotFoundError as exc:
        typer.echo(f"ERROR: {exc}")
        raise typer.Exit(code=1) from exc
    if missing:
        for section in missing:
            typer.echo(f"WARNING: empty brief section: {section}")
        raise typer.Exit(code=1)
    typer.echo(f"OK: brief {series_id}")


@app.command("scaffold")
def scaffold(series_id: str, episode_id: str) -> None:
    """Create an episode scaffold with the complete bilingual shot schema."""
    try:
        path = scaffold_episode(_root(), series_id, episode_id)
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Created authoring scaffold: {path}")


@app.command()
def validate(
    series_id: str,
    episode_id: str | None = typer.Argument(None),
) -> None:
    """Validate a series or one episode."""
    loader = ProjectLoader(_root())
    if not episode_id:
        try:
            series = loader.load_series(series_id)
            loader.load_characters(series_id)
            loader.load_locations(series_id)
            loader.load_style(series)
        except Exception as exc:
            typer.echo(f"ERROR: {exc}")
            raise typer.Exit(code=1) from exc
        typer.echo(f"OK: {series_id}")
        return
    try:
        bundle = loader.load_episode_bundle(series_id, episode_id)
        issues = validate_bundle(bundle)
        report = lint_bundle(bundle, load_production(_root()))
    except Exception as exc:
        typer.echo(f"ERROR: {exc}")
        raise typer.Exit(code=1) from exc
    for issue in issues:
        prefix = issue.level.upper()
        suffix = f" [{issue.shot_id}]" if issue.shot_id else ""
        typer.echo(f"{prefix}{suffix}: {issue.message}")
    Console().print(pacing_table(report))
    if any(issue.level == "error" for issue in issues):
        raise typer.Exit(code=1)
    typer.echo(f"OK: {series_id}/{episode_id}")


@app.command()
def lint(series_id: str, episode_id: str) -> None:
    """Check spoken pacing, intentional silence, beats, and Portuguese mirrors."""
    loader = ProjectLoader(_root())
    try:
        bundle = loader.load_episode_bundle(series_id, episode_id)
        report = lint_bundle(bundle, load_production(_root()))
    except Exception as exc:
        typer.echo(f"ERROR: {exc}")
        raise typer.Exit(code=1) from exc
    for issue in report.issues:
        prefix = issue.level.upper()
        suffix = f" [{issue.shot_id}]" if issue.shot_id else ""
        typer.echo(f"{prefix}{suffix}: {issue.message}")
    Console().print(pacing_table(report))
    if any(issue.level == "error" for issue in report.issues):
        raise typer.Exit(code=1)
    typer.echo(f"OK: pacing {series_id}/{episode_id}")


@app.command()
def prompts(
    series_id: str,
    episode_id: str,
    shot: str | None = typer.Option(None, "--shot"),
    phase: str | None = typer.Option(None, "--phase"),
) -> None:
    """Generate copy-ready prompts for pending shots."""
    if phase not in {None, "images", "videos"}:
        raise typer.BadParameter("phase must be images or videos")
    loader = ProjectLoader(_root())
    try:
        bundle = loader.load_episode_bundle(series_id, episode_id)
        results = write_prompts(_root(), bundle, shot_filter=shot, phase=phase)
    except Exception as exc:
        typer.echo(f"ERROR: {exc}")
        raise typer.Exit(code=1) from exc
    if not results:
        typer.echo("No prompts generated.")
        return
    printed: set[Path] = set()
    shot_ids = {item.id for item in bundle.shots.shots}
    for result in results:
        scene_id = (
            result.shot.id[:-1]
            if result.shot.id.endswith("i") and result.shot.id[:-1] in shot_ids
            else result.shot.id
        )
        target = bundle.episode_dir / "prompts" / f"{scene_id}.md"
        if target not in printed:
            typer.echo(f"Generated {target}")
            printed.add(target)
        for issue in result.issues:
            if issue.level in {"warning", "error"}:
                typer.echo(f"{issue.level.upper()} [{result.shot.id}]: {issue.message}")


@app.command()
def board(series_id: str, episode_id: str) -> None:
    """Write and display the visual production board for an episode."""
    loader = ProjectLoader(_root())
    try:
        bundle = loader.load_episode_bundle(series_id, episode_id)
        target = write_board(bundle)
    except Exception as exc:
        typer.echo(f"ERROR: {exc}")
        raise typer.Exit(code=1) from exc
    typer.echo(f"Board written to {target}")
    typer.echo(target.read_text(encoding="utf-8"))


@app.command()
def next(series_id: str, episode_id: str) -> None:
    """Show the next safe production action and its prompt."""
    loader = ProjectLoader(_root())
    try:
        bundle = loader.load_episode_bundle(series_id, episode_id)
        row = next_row(bundle)
    except Exception as exc:
        typer.echo(f"ERROR: {exc}")
        raise typer.Exit(code=1) from exc
    if row is None:
        typer.echo("Episódio concluído: todos os planos estão aprovados.")
        return
    typer.echo(f"Próxima ação: {row.next_action}")
    typer.echo(f"Plano: {row.shot_id} · Etapa: {row.stage} · Prompt: {row.prompt_file}")
    can_generate = (row.stage == "IMAGE" and "Gerar imagem" in row.next_action) or (
        row.stage == "VIDEO" and "gerar vídeo" in row.next_action
    )
    if not can_generate:
        return
    shot_ids = {item.id for item in bundle.shots.shots}
    scene_id = (
        row.shot_id[:-1]
        if row.shot_id.endswith("i") and row.shot_id[:-1] in shot_ids
        else row.shot_id
    )
    write_prompts(_root(), bundle, shot_filter=row.shot_id)
    prompt_path = bundle.episode_dir / "prompts" / f"{scene_id}.md"
    typer.echo("")
    typer.echo(prompt_path.read_text(encoding="utf-8"))


@app.command()
def credits() -> None:
    """Show configured media costs."""
    config = load_production(_root())
    typer.echo(f"Image: {config.image.credits} credits")
    for duration, cost in sorted(config.video.duration_credits.items()):
        typer.echo(f"Video {duration}s ({config.video.resolution}): {cost} credits")


if __name__ == "__main__":
    app()
