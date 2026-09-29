from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .config import load_accounts, load_production
from .credits import VIDEO_KINDS, build_episode_plan
from .loader import LoadedEpisode
from .models import Shot
from .prompts import render_prompt

DONE_STATUSES = {"approved", "edited"}


@dataclass(frozen=True)
class SessionItem:
    phase: str
    shot_id: str
    what: str
    attachment: str
    prompt: str
    destination: str
    account: str
    cost: int


def _reference_for(bundle: LoadedEpisode, shot: Shot, shots: dict[str, Shot]) -> str:
    parent_id = shot.parent or shot.reference_from
    if not parent_id:
        return "nenhuma (imagem âncora)"
    parent = shots.get(parent_id)
    if not parent:
        return f"imagem do plano {parent_id} (parent ausente)"
    relative = parent.files.image or (
        f"assets/images/{bundle.episode.id.upper()}_{parent_id}_image.jpg"
    )
    return relative


def _destination(bundle: LoadedEpisode, shot: Shot) -> str:
    if shot.kind in {"anchor_image", "derived_image"}:
        return shot.files.image or f"assets/images/{bundle.episode.id.upper()}_{shot.id}_image.jpg"
    return shot.files.video or f"assets/videos/{bundle.episode.id.upper()}_{shot.id}_video.mp4"


def _template_environment(root: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(root / "templates" / "prompts"),
        undefined=StrictUndefined,
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def session_items(
    root: Path,
    bundle: LoadedEpisode,
    account: str | None = None,
) -> list[SessionItem]:
    accounts = {item.id for item in load_accounts(root).accounts}
    if account and account not in accounts:
        raise ValueError(f"Conta '{account}' não existe em config/accounts.yaml")
    plan = build_episode_plan(root, bundle)
    assignments = {item.shot_id: item for item in plan.worst_assignments}
    shots = {shot.id: shot for shot in bundle.shots.shots}
    pending_videos = [
        shot
        for shot in sorted(bundle.shots.shots, key=lambda item: item.order)
        if shot.kind in VIDEO_KINDS and shot.status not in DONE_STATUSES
    ]
    selected: list[tuple[str, Shot, str]] = []
    for shot in sorted(bundle.shots.shots, key=lambda item: item.order):
        if shot.kind in {"anchor_image", "derived_image"}:
            if shot.status in DONE_STATUSES:
                continue
            related_accounts = {
                assignments[item.id].account_id
                for item in pending_videos
                if item.parent == shot.id and item.id in assignments
            }
            if account and account not in related_accounts:
                continue
            selected.append(("IMAGENS", shot, next(iter(related_accounts), "—")))
        elif shot in pending_videos:
            assignment = assignments[shot.id]
            if account and assignment.account_id != account:
                continue
            selected.append(("VÍDEOS", shot, assignment.account_id))

    items: list[SessionItem] = []
    for phase, shot, suggested_account in selected:
        result = render_prompt(root, bundle, shot)
        items.append(
            SessionItem(
                phase=phase,
                shot_id=shot.id,
                what="Gerar imagem" if phase == "IMAGENS" else "Gerar vídeo",
                attachment=_reference_for(bundle, shot, shots),
                prompt=result.prompt,
                destination=_destination(bundle, shot),
                account=suggested_account,
                cost=result.cost,
            )
        )
    return sorted(items, key=lambda item: (item.phase != "IMAGENS", item.shot_id))


def write_session_sheet(
    root: Path,
    bundle: LoadedEpisode,
    account: str | None = None,
) -> Path:
    production = load_production(root)
    profile_name = bundle.profile_name or production.effective_profile_name(
        bundle.series.profile, bundle.episode.profile
    )
    profile = production.profile(profile_name)
    items = session_items(root, bundle, account=account)
    template = _template_environment(root).get_template("session_sheet.j2")
    content = template.render(
        series_title=bundle.series.title,
        episode_id=bundle.episode.id,
        profile_name=profile_name,
        resolution=profile.resolution,
        account_filter=account or "todas",
        items=items,
    )
    target = bundle.episode_dir / "prompts" / "session_sheet.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
