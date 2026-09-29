from __future__ import annotations

import re
from pathlib import Path

from .scaffold import new_episode

BRIEF_SECTIONS: tuple[tuple[str, str], ...] = (
    ("Premissa", "Qual é a premissa em uma frase?"),
    ("Público", "Para quem esta série é feita?"),
    ("Estilo desejado", "Qual estilo visual e tom você deseja?"),
    ("Personagens", "Quem são os personagens e o que cada um quer?"),
    ("Locais", "Quais locais aparecem e o que pode ser filmado neles?"),
    ("Número de episódios", "Quantos episódios a temporada terá?"),
    ("Gancho de temporada", "Qual pergunta ou revelação puxa a próxima etapa?"),
    ("O que não quero", "Quais temas, imagens ou soluções devem ser evitados?"),
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
    return content.strip()


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
