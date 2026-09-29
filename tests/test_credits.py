from datetime import date, timedelta
from pathlib import Path

import pytest

from studio.config import load_production, show_first_run_warning
from studio.credits import build_day_plan, build_episode_plan
from studio.loader import ProjectLoader

ROOT = Path(__file__).parents[1]


def test_episode_plan_has_expected_and_worst_case_budgets() -> None:
    bundle = ProjectLoader(ROOT).load_episode_bundle("revenge_republic", "ep01")

    report = build_episode_plan(ROOT, bundle)

    assert [item.shot.id for item in report.items] == ["P04", "P05", "P06"]
    assert report.expected_total == 15
    assert report.worst_total == 30
    assert report.max_attempts == 2
    assert report.assignment_for("P04") is not None


def test_day_plan_reports_episode_and_video_capacity() -> None:
    report = build_day_plan(ROOT, requested_episodes=1)

    assert report.expected_episodes_per_day >= 1
    assert report.expected_videos_per_day == (
        report.expected_episodes_per_day * report.videos_per_episode
    )
    assert report.requested_expected_fits is True
    assert report.requested_worst_fits is True


def test_unknown_resolution_cost_fails_in_portuguese() -> None:
    production = load_production(ROOT)

    with pytest.raises(ValueError, match="Preencha o custo de 1080p"):
        production.video_credits(8, resolution="1080p")


def test_stale_cost_warning_uses_configured_age() -> None:
    production = load_production(ROOT).model_copy(deep=True)
    production.video.costs_verified_on = date.today() - timedelta(days=31)
    production.video.costs_max_age_days = 30

    assert production.costs_warning() == "Conferir custos na interface do Flow: eles mudam"


def test_terms_warning_is_shown_once_and_persisted(tmp_path: Path, capsys) -> None:
    assert show_first_run_warning(tmp_path) is True
    assert show_first_run_warning(tmp_path) is False

    output = capsys.readouterr().out
    assert "pode violar os termos" in output
    assert (tmp_path / ".studio_state.json").exists()
