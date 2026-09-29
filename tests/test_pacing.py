from dataclasses import replace
from pathlib import Path

from studio.config import load_production
from studio.loader import ProjectLoader
from studio.models import DialogueLine, Shot, ShotsFile
from studio.pacing import lint_bundle, shot_words

ROOT = Path(__file__).parents[1]


def _bundle_with(*shots: Shot):
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    return replace(bundle, shots=ShotsFile(shots=list(shots)))


def _video(shot_id: str = "P99", **updates: object) -> Shot:
    values: dict[str, object] = {
        "id": shot_id,
        "order": 0,
        "kind": "video_from_image",
        "location": "kitchen",
        "framing": "medium shot",
        "framing_pt": "plano médio",
        "action": "a visible action",
        "action_pt": "uma ação visível",
        "duration_s": 8,
        "beat_pt": "uma mudança concreta",
    }
    values.update(updates)
    return Shot.model_validate(values)


def _messages(report, level: str | None = None, shot_id: str | None = None) -> list[str]:
    return [
        issue.message
        for issue in report.issues
        if (level is None or issue.level == level) and (shot_id is None or issue.shot_id == shot_id)
    ]


def test_video_without_speech_is_an_error() -> None:
    report = lint_bundle(_bundle_with(_video()), load_production(ROOT))
    assert any("needs dialogue_pt" in message for message in _messages(report, "error"))


def test_speech_longer_than_duration_is_an_error() -> None:
    line = DialogueLine(speaker="duda", text="uma " * 25)
    report = lint_bundle(_bundle_with(_video(dialogue_pt=[line])), load_production(ROOT))
    assert any("exceeds duration" in message for message in _messages(report, "error"))


def test_underfilled_speech_reports_empty_seconds() -> None:
    line = DialogueLine(speaker="duda", text="Uma revelação curta")
    report = lint_bundle(_bundle_with(_video(dialogue_pt=[line])), load_production(ROOT))
    assert any("remain empty" in message for message in _messages(report, "warning"))


def test_long_line_and_line_count_are_warnings() -> None:
    lines = [DialogueLine(speaker="duda", text="uma " * 16) for _ in range(3)]
    report = lint_bundle(_bundle_with(_video(dialogue_pt=lines)), load_production(ROOT))
    warnings = _messages(report, "warning")
    assert any("spoken lines exceed" in message for message in warnings)
    assert sum("maximum is 15" in message for message in warnings) == 3


def test_voice_over_counts_as_speech() -> None:
    shot = _video(
        dialogue_pt=[],
        voice_over_pt=[DialogueLine(speaker="duda", text="A prova está comigo")],
    )
    report = lint_bundle(_bundle_with(shot), load_production(ROOT))
    assert shot_words(shot) == 4
    assert not any("needs dialogue_pt" in message for message in _messages(report, "error"))


def test_intentional_silence_is_allowed_but_episode_limit_warns() -> None:
    shots = [
        _video("P01", intentional_silence=True, beat_pt="primeiro golpe"),
        _video("P02", order=1, intentional_silence=True, beat_pt="segundo golpe"),
    ]
    report = lint_bundle(_bundle_with(*shots), load_production(ROOT))
    assert not _messages(report, "error")
    assert any("intentional silences" in message for message in _messages(report, "warning"))


def test_empty_and_repeated_beats_are_warnings() -> None:
    shots = [
        _video("P01", beat_pt=""),
        _video(
            "P02",
            order=1,
            beat_pt="mesmo golpe",
            dialogue_pt=[DialogueLine(speaker="duda", text="Vai")],
        ),
        _video(
            "P03",
            order=2,
            beat_pt="mesmo golpe",
            dialogue_pt=[DialogueLine(speaker="duda", text="Agora")],
        ),
    ]
    report = lint_bundle(_bundle_with(*shots), load_production(ROOT))
    warnings = _messages(report, "warning")
    assert "beat_pt is empty" in warnings
    assert "Consecutive shots repeat the same beat_pt" in warnings


def test_missing_portuguese_mirror_is_a_warning() -> None:
    shot = _video(framing_pt="")
    report = lint_bundle(_bundle_with(shot), load_production(ROOT))
    assert any("framing_pt" in message for message in _messages(report, "warning"))


def test_missing_direction_mirror_is_a_warning() -> None:
    shot = _video(setup="A room", setup_pt="")
    report = lint_bundle(_bundle_with(shot), load_production(ROOT))
    assert any("setup_pt" in message for message in _messages(report, "warning"))
