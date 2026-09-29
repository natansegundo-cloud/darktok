from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from rich.table import Table

from .config import load_production, read_yaml
from .models import ProductionConfig, Series

BIBLE_SECTIONS: tuple[str, ...] = (
    "Premissa em uma frase (a frase que faria alguém parar de rolar)",
    "Por que alguém volta amanhã (motor de retenção: pergunta aberta, segredo, escalada)",
    "Regra visual (o que é \"estranho\" nesta série e o que NUNCA muda)",
    "Personagens (para cada um: quer / esconde / silhueta absurda)",
    "Mundo e regras (o que é possível e o que não é)",
    "Arco da temporada (começo, virada do meio, revelação final)",
    "Grade de episódios (tabela: nº | abertura já no meio da ação | virada | cliffhanger)",
    "Bordão ou motivo recorrente (algo repetido que vira marca e vira comentário)",
    "Tom e limites (o que a série não faz; nada que viole as regras da plataforma)",
    "Referências (apenas descrição de sensações, nunca personagens ou pessoas existentes)",
)


@dataclass(frozen=True)
class BibleIssue:
    level: str
    message: str


@dataclass(frozen=True)
class BibleReport:
    series_id: str
    status: str
    section_stats: tuple[tuple[str, int, str], ...]
    episode_rows: int
    episodes_planned: int
    issues: tuple[BibleIssue, ...]


def _without_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def section_content(text: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return ""
    rest = text[match.end() :]
    next_heading = re.search(r"^##\s+", rest, flags=re.MULTILINE)
    return (rest[: next_heading.start()] if next_heading else rest).strip()


def _normalise(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    without_punctuation = re.sub(r"[^\w\s]", " ", without_accents.casefold())
    return re.sub(r"\s+", " ", without_punctuation).strip()


def _episode_rows(content: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        row_text = stripped[1:]
        if row_text.endswith("|"):
            row_text = row_text[:-1]
        cells = [cell.strip() for cell in row_text.split("|")]
        if len(cells) < 4:
            continue
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        if _normalise(cells[0]) in {"n", "no", "numero"}:
            continue
        rows.append(cells)
    return rows


def _production_config(root: Path) -> ProductionConfig:
    try:
        return load_production(root)
    except FileNotFoundError:
        return ProductionConfig()


def check_bible(root: Path, series_id: str) -> BibleReport:
    series_path = root / "series" / series_id / "series.yaml"
    bible_path = root / "series" / series_id / "bible.md"
    issues: list[BibleIssue] = []
    section_stats: list[tuple[str, int, str]] = []
    production = _production_config(root)
    config = production.bible

    try:
        series = Series.model_validate(read_yaml(series_path))
    except (FileNotFoundError, ValueError) as exc:
        return BibleReport(
            series_id=series_id,
            status="unknown",
            section_stats=(),
            episode_rows=0,
            episodes_planned=0,
            issues=(BibleIssue("error", f"Não foi possível ler series.yaml: {exc}"),),
        )

    if not bible_path.exists():
        issues.append(BibleIssue("error", f"Bíblia não encontrada: {bible_path}"))
        return BibleReport(
            series_id=series_id,
            status=series.status,
            section_stats=(),
            episode_rows=0,
            episodes_planned=series.episodes_planned,
            issues=tuple(issues),
        )

    text = bible_path.read_text(encoding="utf-8")
    contents: dict[str, str] = {}
    for heading in BIBLE_SECTIONS:
        content = section_content(text, heading)
        contents[heading] = content
        if not content:
            issues.append(BibleIssue("error", f"Seção obrigatória ausente: {heading}"))
            section_stats.append((heading, 0, "erro"))
            continue
        visible = _without_comments(content).strip()
        length = len(visible)
        status = "ok"
        if length < config.min_section_chars:
            issues.append(
                BibleIssue(
                    "error",
                    f"Seção '{heading}' tem {length} caracteres; "
                    f"mínimo: {config.min_section_chars}.",
                )
            )
            status = "erro"
        for marker in config.placeholder_markers:
            if marker and marker.casefold() in visible.casefold():
                issues.append(
                    BibleIssue(
                        "error",
                        f"Marcador de placeholder '{marker}' encontrado na seção '{heading}'.",
                    )
                )
                status = "erro"
        section_stats.append((heading, length, status))

    grade_heading = BIBLE_SECTIONS[6]
    rows = _episode_rows(_without_comments(contents.get(grade_heading, "")))
    if len(rows) < series.episodes_planned:
        issues.append(
            BibleIssue(
                "error",
                f"Grade de episódios tem {len(rows)} linhas; esperado: {series.episodes_planned}.",
            )
        )
    previous_cliffhanger: str | None = None
    for index, row in enumerate(rows, start=1):
        cliffhanger = row[3].strip()
        if not cliffhanger:
            issues.append(BibleIssue("error", f"Episódio {index} está sem cliffhanger."))
        normalised = _normalise(cliffhanger)
        if previous_cliffhanger and normalised == previous_cliffhanger:
            issues.append(
                BibleIssue(
                    "warning",
                    f"Cliffhanger do episódio {index} repete o do episódio {index - 1}.",
                )
            )
        if normalised:
            previous_cliffhanger = normalised

    return BibleReport(
        series_id=series_id,
        status=series.status,
        section_stats=tuple(section_stats),
        episode_rows=len(rows),
        episodes_planned=series.episodes_planned,
        issues=tuple(issues),
    )


def bible_table(report: BibleReport) -> Table:
    table = Table(title=f"Verificação da bíblia · {report.series_id}")
    table.add_column("Seção")
    table.add_column("Caracteres", justify="right")
    table.add_column("Status")
    for heading, length, status in report.section_stats:
        table.add_row(heading, str(length), status)
    table.add_row(
        "Grade de episódios",
        f"{report.episode_rows}/{report.episodes_planned} linhas",
        "ok" if report.episode_rows >= report.episodes_planned else "erro",
    )
    return table


def has_bible_errors(report: BibleReport) -> bool:
    return any(issue.level == "error" for issue in report.issues)
