from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import load_production
from .loader import LoadedEpisode
from .models import Shot


@dataclass(frozen=True)
class BoardRow:
    order: int
    shot_id: str
    stage: str
    status: str
    source_image: str
    video_file: str
    prompt_file: str
    cost: str
    next_action: str


def _file_label(episode_dir: Path, relative: str | None) -> str:
    if not relative:
        return "—"
    path = episode_dir / relative
    marker = "OK" if path.exists() else "MISSING"
    return f"`{relative}` ({marker})"


def _status_label(shot: Shot | None) -> str:
    return shot.status if shot else "missing"


def _next_action(episode_dir: Path, shot: Shot, parent: Shot | None) -> str:
    if shot.kind in {"anchor_image", "derived_image"}:
        if shot.status in {"approved", "edited"}:
            if shot.files.image and (episode_dir / shot.files.image).exists():
                return "Imagem concluída"
            return f"Colocar imagem em {shot.files.image or 'assets/images/'}"
        scene_id = shot.id[:-1] if shot.id.endswith("i") else shot.id
        return f"Gerar imagem · copiar prompts/{scene_id}.md, seção IMAGEM"
    if not parent:
        return "Corrigir parent da imagem"
    if parent.status not in {"approved", "edited"}:
        return f"Aguardar aprovação de {parent.id}"
    if not parent.files.image or not (episode_dir / parent.files.image).exists():
        return f"Colocar imagem aprovada de {parent.id} em {parent.files.image or 'assets/images/'}"
    if shot.status in {"approved", "edited"}:
        return "Vídeo concluído"
    return f"Anexar {parent.id} e gerar vídeo"


def board_rows(bundle: LoadedEpisode) -> list[BoardRow]:
    shots = {shot.id: shot for shot in bundle.shots.shots}
    production = load_production(bundle.series_dir.parent.parent)
    rows: list[BoardRow] = []
    for shot in sorted(bundle.shots.shots, key=lambda item: item.order):
        parent = shots.get(shot.parent) if shot.parent else None
        is_image = shot.kind in {"anchor_image", "derived_image"}
        scene_id = shot.id[:-1] if is_image and shot.id[:-1] in shots else shot.id
        source = shot.files.image if is_image else (parent.files.image if parent else None)
        video = shot.files.video if not is_image else None
        status = shot.status if is_image else (
            f"imagem {_status_label(parent)} / vídeo {shot.status}"
        )
        cost = "0" if is_image else str(production.video_credits(shot.duration_s))
        rows.append(
            BoardRow(
                order=shot.order,
                shot_id=shot.id,
                stage="IMAGE" if is_image else "VIDEO",
                status=status,
                source_image=_file_label(bundle.episode_dir, source),
                video_file=_file_label(bundle.episode_dir, video),
                prompt_file=f"`prompts/{scene_id}.md`",
                cost=cost,
                next_action=_next_action(bundle.episode_dir, shot, parent),
            )
        )
    return rows


def render_board(bundle: LoadedEpisode) -> str:
    rows = board_rows(bundle)
    lines = [
        f"# Production board — {bundle.series.title} · {bundle.episode.id}",
        "",
        "> Use `studio next` para executar somente a próxima ação. `MISSING` indica que o "
        "caminho foi registrado, mas o arquivo ainda não está na pasta.",
        "",
        "| Ordem | Plano | Etapa | Status | Imagem de origem | Vídeo | Prompt | "
        "Créditos | Próxima ação |",
        "| ---: | --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.order} | **{row.shot_id}** | {row.stage} | {row.status} | "
            f"{row.source_image} | {row.video_file} | {row.prompt_file} | "
            f"{row.cost} | {row.next_action} |"
        )
    lines.extend(
        [
            "",
            "## Regra do fluxo",
            "",
            "`P03i` é a imagem. `P03` é o vídeo que deve anexar a imagem `P03i`.",
            "O vídeo só deve ser gerado depois que a imagem de origem estiver aprovada.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_board(bundle: LoadedEpisode) -> Path:
    target = bundle.episode_dir / "production_board.md"
    target.write_text(render_board(bundle), encoding="utf-8")
    return target


def next_row(bundle: LoadedEpisode) -> BoardRow | None:
    for row in board_rows(bundle):
        if row.next_action not in {"Imagem concluída", "Vídeo concluído"}:
            return row
    return None
