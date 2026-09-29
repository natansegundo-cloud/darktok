from pathlib import Path

from studio.config import load_production
from studio.loader import ProjectLoader

ROOT = Path(__file__).parents[1]


def test_video_costs_are_configured_by_duration() -> None:
    config = load_production(ROOT)
    assert config.image.credits == 0
    assert config.video_credits(6) == 5
    assert config.video_credits(8) == 6
    assert config.video_credits(10) == 7


def test_example_bundle_loads() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    assert bundle.series.style == "realistic_drama"
    assert bundle.series.status == "paused"
    assert "fixture" in bundle.series.notes.lower()
    assert bundle.episode.cold_open.source_shot == "P01"
    assert len(bundle.shots.shots) == 12


def test_pacing_and_authoring_fields_are_optional() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    shot = bundle.shots.shots[0]
    assert shot.voice_over_pt == []
    assert shot.intentional_silence is False
    assert shot.beat_pt
    assert load_production(ROOT).pacing.words_per_second == 2.5
    assert load_production(ROOT).pacing.enforcement.low_fill == "error"
    assert load_production(ROOT).pacing.delivery_forbidden_markers


def test_delivery_fields_are_optional_and_character_defaults_are_loaded() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    line = next(item for item in bundle.shots.shots if item.id == "P01").dialogue_pt[0]
    duda = next(item for item in bundle.characters.characters if item.id == "duda")
    assert line.delivery == "low, cold, controlled"
    assert line.delivery_pt == "baixa, fria, controlada"
    assert duda.default_delivery == "low, cold, controlled"
    assert duda.default_delivery_pt == "baixa, fria, controlada"


def test_example_video_has_timed_direction() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")
    shot = next(item for item in bundle.shots.shots if item.id == "P03")
    assert shot.setup_pt
    assert shot.start_state_pt
    assert len(shot.timeline_pt) == 4
    assert shot.end_state_pt
    assert shot.sound_pt
    assert shot.must_not_pt
