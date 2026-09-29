import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

from studio.config import load_production
from studio.loader import ProjectLoader

ROOT = Path(__file__).parents[1]


def test_video_costs_are_configured_by_duration() -> None:
    config = load_production(ROOT)
    assert config.image.credits == 0
    assert config.video_credits(6) == 5
    assert config.video_credits(8) == 6
    assert config.video_credits(10) == 7


def test_profiles_and_unknown_resolution_cost_are_configured() -> None:
    config = load_production(ROOT)
    assert config.active_profile == "growth"
    assert config.profile("growth").resolution == "360p"
    assert config.profile("monetize").episode_seconds.min == 61
    with pytest.raises(ValueError, match="Preencha o custo de 1080p"):
        config.video_credits(8, resolution="1080p")


def test_stale_cost_verification_warns() -> None:
    config = load_production(ROOT)
    stale_video = config.video.model_copy(
        update={"costs_verified_on": date.today() - timedelta(days=31)}
    )
    stale = config.model_copy(update={"video": stale_video})
    assert stale.costs_warning() == "Conferir custos na interface do Flow: eles mudam"
    assert config.costs_warning() == "Conferir custos na interface do Flow: eles mudam"


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


def test_profile_precedence_episode_then_series_then_config(tmp_path: Path) -> None:
    for directory in ("config", "series", "styles"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    series_path = tmp_path / "series" / "revenge_republic" / "series.yaml"
    episode_path = (
        tmp_path / "series" / "revenge_republic" / "episodes" / "ep01" / "episode.yaml"
    )
    series_data = yaml.safe_load(series_path.read_text(encoding="utf-8"))
    episode_data = yaml.safe_load(episode_path.read_text(encoding="utf-8"))
    series_data["profile"] = "monetize"
    episode_data["profile"] = "growth"
    series_path.write_text(
        yaml.safe_dump(series_data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    episode_path.write_text(
        yaml.safe_dump(episode_data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    loader = ProjectLoader(tmp_path)
    assert loader.load_episode_bundle("revenge_republic", "ep01").profile_name == "growth"
    episode_data["profile"] = None
    episode_path.write_text(
        yaml.safe_dump(episode_data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    assert loader.load_episode_bundle("revenge_republic", "ep01").profile_name == "monetize"
    series_data["profile"] = None
    series_path.write_text(
        yaml.safe_dump(series_data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    assert loader.load_episode_bundle("revenge_republic", "ep01").profile_name == "growth"


def test_character_silhouette_and_safety_fields_load() -> None:
    from studio.models import Character, SafetyConfig

    character = Character(
        id="odd",
        name="Odd",
        lock_block="Odd, a person with a triangular nose",
        silhouette_hook="triangular nose",
        silhouette_hook_pt="nariz triangular",
        palette="violet and mustard",
    )
    assert character.silhouette_hook == "triangular nose"
    assert character.palette == "violet and mustard"
    assert SafetyConfig().blocked_terms == []
