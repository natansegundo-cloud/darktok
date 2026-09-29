from __future__ import annotations

import re
from dataclasses import dataclass

from rich.table import Table

from .loader import LoadedEpisode
from .models import ProductionConfig, Shot, ValidationIssue

VIDEO_KINDS = {"video_from_image", "video_expression_only"}
WORD_RE = re.compile(r"\b[\wÀ-ÖØ-öø-ÿ]+(?:['’\-][\wÀ-ÖØ-öø-ÿ]+)*\b")


@dataclass(frozen=True)
class PacingRow:
    shot_id: str
    kind: str
    words: int
    speech_seconds: float
    fill_percent: float
    empty_seconds: float


@dataclass(frozen=True)
class PacingReport:
    rows: list[PacingRow]
    issues: list[ValidationIssue]


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def shot_words(shot: Shot) -> int:
    lines = [*shot.dialogue_pt, *shot.voice_over_pt]
    return sum(count_words(line.text) for line in lines)


def _issue(level: str, message: str, shot_id: str | None = None) -> ValidationIssue:
    return ValidationIssue(level=level, message=message, shot_id=shot_id)


def _missing_pt_issues(bundle: LoadedEpisode, shot: Shot) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    def check(english: str, portuguese: str, field: str) -> None:
        if not english or portuguese.strip():
            return
        issues.append(_issue("warning", f"Missing Portuguese mirror: {field}_pt", shot.id))

    check(shot.framing, shot.framing_pt, "framing")
    if shot.action or shot.action_en:
        check(shot.action or shot.action_en, shot.action_pt, "action")
    if shot.camera:
        check(shot.camera, shot.camera_pt, "camera")
    if shot.gaze:
        check(shot.gaze, shot.gaze_pt, "gaze")
    if shot.mood:
        check(shot.mood, shot.mood_pt, "mood")
    if shot.expression:
        check(shot.expression, shot.expression_pt, "expression")
    if shot.light:
        check(shot.light, shot.light_pt, "light")

    location = next((item for item in bundle.locations.locations if item.id == shot.location), None)
    if location:
        if location.description_en:
            check(location.description_en, location.description_pt, "description")
        if location.default_light:
            check(location.default_light, location.default_light_pt, "default_light")
    characters = {item.id: item for item in bundle.characters.characters}
    for character_id in shot.characters:
        character = characters.get(character_id)
        if character and character.lock_block:
            check(character.lock_block, character.lock_block_pt, "lock_block")

    style = bundle.style
    for english, portuguese, field in (
        (style.style_block, style.style_block_pt, "style_block"),
        (style.negative_hints, style.negative_hints_pt, "negative_hints"),
        (style.camera_defaults, style.camera_defaults_pt, "camera_defaults"),
        (style.video_motion_defaults, style.video_motion_defaults_pt, "video_motion_defaults"),
        (style.character_rules, style.character_rules_pt, "character_rules"),
    ):
        check(english, portuguese, field)
    return issues


def _direction_issues(shot: Shot) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for english, portuguese, field in (
        (shot.setup, shot.setup_pt, "setup"),
        (shot.start_state, shot.start_state_pt, "start_state"),
        (shot.end_state, shot.end_state_pt, "end_state"),
        (shot.sound, shot.sound_pt, "sound"),
        (shot.must_not, shot.must_not_pt, "must_not"),
    ):
        if english and not portuguese:
            issues.append(_issue("warning", f"Missing Portuguese mirror: {field}_pt", shot.id))
        if portuguese and not english:
            issues.append(_issue("warning", f"Missing English direction field: {field}", shot.id))

    if shot.timeline and not shot.timeline_pt:
        issues.append(_issue("warning", "Missing Portuguese mirror: timeline_pt", shot.id))
    if shot.timeline_pt and not shot.timeline:
        issues.append(_issue("warning", "Missing English direction field: timeline", shot.id))
    if len(shot.timeline) != len(shot.timeline_pt) and shot.timeline and shot.timeline_pt:
        issues.append(_issue("warning", "timeline and timeline_pt have different lengths", shot.id))
    for index, beat in enumerate(shot.timeline):
        if beat.action and not beat.action_pt:
            issues.append(
                _issue(
                    "warning",
                    f"Missing Portuguese mirror: timeline[{index}].action_pt",
                    shot.id,
                )
            )
    return issues


def lint_bundle(bundle: LoadedEpisode, production: ProductionConfig) -> PacingReport:
    config = production.pacing
    rows: list[PacingRow] = []
    issues: list[ValidationIssue] = []
    ordered = sorted(bundle.shots.shots, key=lambda item: item.order)
    previous_beat = ""
    intentional_count = 0

    for shot in ordered:
        words = shot_words(shot)
        is_video = shot.kind in VIDEO_KINDS
        duration = float(shot.duration_s) if is_video else 0.0
        speech_seconds = words / config.words_per_second if config.words_per_second else 0.0
        empty_seconds = max(duration - speech_seconds, 0.0)
        fill_percent = (speech_seconds / duration * 100) if duration else 0.0
        rows.append(
            PacingRow(
                shot_id=shot.id,
                kind=shot.kind,
                words=words,
                speech_seconds=speech_seconds,
                fill_percent=fill_percent,
                empty_seconds=empty_seconds,
            )
        )

        if not shot.beat_pt.strip():
            issues.append(_issue("warning", "beat_pt is empty", shot.id))
        elif previous_beat and shot.beat_pt.strip() == previous_beat:
            issues.append(_issue("warning", "Consecutive shots repeat the same beat_pt", shot.id))
        previous_beat = shot.beat_pt.strip()

        issues.extend(_missing_pt_issues(bundle, shot))
        if not is_video:
            continue

        issues.extend(_direction_issues(shot))

        lines = [*shot.dialogue_pt, *shot.voice_over_pt]
        if not lines and not shot.intentional_silence:
            issues.append(
                _issue(
                    "error",
                    "Video shot needs dialogue_pt, voice_over_pt, or intentional_silence",
                    shot.id,
                )
            )
        if speech_seconds > duration:
            issues.append(
                _issue(
                    "error",
                    f"Estimated speech ({speech_seconds:.1f}s) exceeds duration ({duration:.1f}s)",
                    shot.id,
                )
            )
        if speech_seconds < config.min_speech_fill * duration:
            issues.append(
                _issue(
                    "warning",
                    f"Estimated speech fills {speech_seconds:.1f}s; "
                    f"{empty_seconds:.1f}s remain empty",
                    shot.id,
                )
            )
        if empty_seconds > config.max_silence_s and not shot.intentional_silence:
            issues.append(
                _issue(
                    "warning",
                    f"Estimated silence ({empty_seconds:.1f}s) exceeds max_silence_s "
                    f"({config.max_silence_s:.1f}s)",
                    shot.id,
                )
            )
        if len(lines) > config.max_dialogue_lines:
            issues.append(
                _issue(
                    "warning",
                    f"{len(lines)} spoken lines exceed max_dialogue_lines "
                    f"({config.max_dialogue_lines})",
                    shot.id,
                )
            )
        for line in lines:
            words_in_line = count_words(line.text)
            if words_in_line > config.max_words_per_line:
                issues.append(
                    _issue(
                        "warning",
                        f"Line by {line.speaker} has {words_in_line} words; maximum is "
                        f"{config.max_words_per_line}",
                        shot.id,
                    )
                )
        if shot.intentional_silence:
            intentional_count += 1

    if intentional_count > config.max_intentional_silences_per_episode:
        issues.append(
            _issue(
                "warning",
                f"Episode has {intentional_count} intentional silences; maximum is "
                f"{config.max_intentional_silences_per_episode}",
            )
        )
    return PacingReport(rows=rows, issues=issues)


def pacing_table(report: PacingReport) -> Table:
    table = Table(title="Pacing lint")
    table.add_column("Plano")
    table.add_column("Tipo")
    table.add_column("Palavras", justify="right")
    table.add_column("Fala (s)", justify="right")
    table.add_column("Preenchimento", justify="right")
    table.add_column("Vazio (s)", justify="right")
    for row in report.rows:
        table.add_row(
            row.shot_id,
            row.kind,
            str(row.words),
            f"{row.speech_seconds:.1f}",
            f"{row.fill_percent:.0f}%",
            f"{row.empty_seconds:.1f}",
        )
    return table
