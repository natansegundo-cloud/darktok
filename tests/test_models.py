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
    assert bundle.episode.cold_open.source_shot == "P01"
    assert len(bundle.shots.shots) == 12
