from __future__ import annotations

import re
from pathlib import Path

from .bible import BIBLE_SECTIONS
from .scaffold import new_episode

BRIEF_SECTIONS: tuple[tuple[str, str], ...] = tuple(
    (heading, f"Como você responde a esta seção? {heading}?") for heading in BIBLE_SECTIONS
) + (
    (
        "Imagem mais estranha e memorável",
        "Qual é a imagem (cena) mais estranha e memorável da série?",
    ),
    ("Pergunta no fim do episódio 1", "Qual pergunta o espectador faz no fim do ep 1?"),
)


def brief_template(series_id: str) -> str:
    lines = [
        f"# Brief da série: {series_id}",
        "",
        "Preencha as perguntas abaixo em português. O agente transforma este brief em YAML, "
        "roteiro e planos.",
        "",
    ]
    for title, question in BRIEF_SECTIONS:
        lines.extend([f"## {title}", "", f"{question}", "", ""])
    return "\n".join(lines)


def create_brief(root: Path, series_id: str) -> Path:
    series_dir = root / "series" / series_id
    if not series_dir.exists():
        raise FileNotFoundError(f"Series does not exist: {series_id}")
    target = series_dir / "brief_pt.md"
    if target.exists():
        raise FileExistsError(f"Brief already exists: {target}")
    target.write_text(brief_template(series_id), encoding="utf-8")
    return target


def _section_content(text: str, title: str) -> str:
    pattern = rf"^##\s+{re.escape(title)}\s*$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return ""
    rest = text[match.end() :]
    next_heading = re.search(r"^##\s+", rest, flags=re.MULTILINE)
    content = rest[: next_heading.start()] if next_heading else rest
    return re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL).strip()


def check_brief(root: Path, series_id: str) -> list[str]:
    path = root / "series" / series_id / "brief_pt.md"
    if not path.exists():
        raise FileNotFoundError(f"Brief does not exist: {path}")
    text = path.read_text(encoding="utf-8")
    return [
        title
        for title, question in BRIEF_SECTIONS
        if _section_content(text, title) in {"", question}
    ]


def scaffold_episode(root: Path, series_id: str, episode_id: str) -> Path:
    match = re.fullmatch(r"ep(\d{2})", episode_id)
    if not match:
        raise ValueError("episode must use the format epNN, for example ep01")
    return new_episode(root, series_id, int(match.group(1)))
