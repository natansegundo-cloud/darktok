from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from pathlib import Path

from rich.table import Table

from .allocator import AllocationError, AllocationItem, Assignment, allocate
from .config import load_accounts, load_production
from .loader import LoadedEpisode, ProjectLoader
from .models import ProductionConfig, Shot

VIDEO_KINDS = {"video_from_image", "video_expression_only"}
DONE_STATUSES = {"approved", "edited"}


@dataclass(frozen=True)
class BudgetItem:
    shot: Shot
    resolution: str
    cost: int

    @property
    def expected_credits(self) -> int:
        return self.cost


@dataclass(frozen=True)
class EpisodeCreditPlan:
    items: tuple[BudgetItem, ...]
    expected_assignments: tuple[Assignment, ...]
    worst_assignments: tuple[Assignment, ...]
    expected_total: int
    worst_total: int
    expected_days: int
    worst_days: int
    account_ids: tuple[str, ...]
    daily_credits: int
    max_attempts: int

    def assignment_for(self, shot_id: str) -> Assignment | None:
        return next(
            (item for item in self.worst_assignments if item.shot_id == shot_id), None
        )

    def remaining_credits(self, total: int, days: int) -> int:
        return max(days * len(self.account_ids) * self.daily_credits - total, 0)


@dataclass(frozen=True)
class DayPlan:
    profile_name: str
    average_episode_seconds: float
    average_clip_seconds: float
    videos_per_episode: int
    expected_episode_credits: int
    worst_episode_credits: int
    expected_episodes_per_day: int
    worst_episodes_per_day: int
    expected_videos_per_day: int
    worst_videos_per_day: int
    requested_episodes: int | None
    requested_expected_fits: bool | None
    requested_worst_fits: bool | None


def pending_video_shots(bundle: LoadedEpisode) -> list[Shot]:
    return [
        shot
        for shot in sorted(bundle.shots.shots, key=lambda item: item.order)
        if shot.kind in VIDEO_KINDS and shot.status not in DONE_STATUSES
    ]


def budget_items(bundle: LoadedEpisode, production: ProductionConfig) -> list[BudgetItem]:
    profile_name = bundle.profile_name or production.effective_profile_name(
        bundle.series.profile, bundle.episode.profile
    )
    profile = production.profile(profile_name)
    return [
        BudgetItem(
            shot=shot,
            resolution=profile.resolution,
            cost=production.video_credits(shot.duration_s, resolution=profile.resolution),
        )
        for shot in pending_video_shots(bundle)
    ]


def build_episode_plan(root: Path, bundle: LoadedEpisode) -> EpisodeCreditPlan:
    production = load_production(root)
    items = budget_items(bundle, production)
    accounts = load_accounts(root).accounts
    account_ids = tuple(account.id for account in accounts)
    daily_credits = production.accounts.daily_credits_per_account
    reserve = production.accounts.reserve_videos_per_account
    attempts = max(production.video.max_attempts, 1)
    allocation_items = [AllocationItem(item.shot.id, item.cost) for item in items]
    expected = allocate(
        allocation_items,
        list(account_ids),
        daily_credits,
        reserve,
        1,
    )
    worst = allocate(
        allocation_items,
        list(account_ids),
        daily_credits,
        reserve,
        attempts,
    )
    return EpisodeCreditPlan(
        items=tuple(items),
        expected_assignments=tuple(expected),
        worst_assignments=tuple(worst),
        expected_total=sum(item.cost for item in items),
        worst_total=sum(item.cost * attempts for item in items),
        expected_days=max((item.day for item in expected), default=0),
        worst_days=max((item.day for item in worst), default=0),
        account_ids=account_ids,
        daily_credits=daily_credits,
        max_attempts=attempts,
    )


def plan_table(plan: EpisodeCreditPlan) -> Table:
    assignments = {item.shot_id: item for item in plan.worst_assignments}
    table = Table(title="Plano de créditos — pior caso reservado")
    table.add_column("Plano")
    table.add_column("Duração", justify="right")
    table.add_column("Créditos", justify="right")
    table.add_column("Conta")
    table.add_column("Dia", justify="right")
    for item in plan.items:
        assignment = assignments[item.shot.id]
        table.add_row(
            item.shot.id,
            f"{item.shot.duration_s}s",
            str(item.cost),
            assignment.account_id,
            str(assignment.day),
        )
    if not plan.items:
        table.add_row("—", "—", "0", "—", "—")
    return table


def plan_summary(plan: EpisodeCreditPlan) -> list[str]:
    return [
        f"Total esperado (1 tentativa): {plan.expected_total} créditos",
        f"Total pior caso ({plan.max_attempts} tentativas máximas): "
        f"{plan.worst_total} créditos",
        f"Dias necessários: esperado {plan.expected_days}; pior caso {plan.worst_days}",
        "Créditos que sobram: "
        f"esperado {plan.remaining_credits(plan.expected_total, plan.expected_days)}; "
        f"pior caso {plan.remaining_credits(plan.worst_total, plan.worst_days)}",
    ]


def _real_video_durations(root: Path) -> list[int]:
    durations: list[int] = []
    series_root = root / "series"
    if not series_root.exists():
        return durations
    loader = ProjectLoader(root)
    for series_dir in sorted(path for path in series_root.iterdir() if path.is_dir()):
        episodes_dir = series_dir / "episodes"
        if not episodes_dir.exists():
            continue
        for episode_dir in sorted(path for path in episodes_dir.iterdir() if path.is_dir()):
            try:
                bundle = loader.load_episode_bundle(series_dir.name, episode_dir.name)
            except Exception:
                continue
            durations.extend(
                shot.duration_s for shot in bundle.shots.shots if shot.kind in VIDEO_KINDS
            )
    return durations


def _one_day_episode_capacity(
    costs: list[int], account_ids: list[str], production: ProductionConfig, attempts: int
) -> int:
    count = 0
    while True:
        candidate = [
            AllocationItem(f"episode-{episode}-{index}", cost)
            for episode in range(count + 1)
            for index, cost in enumerate(costs)
        ]
        try:
            allocate(
                candidate,
                account_ids,
                production.accounts.daily_credits_per_account,
                production.accounts.reserve_videos_per_account,
                attempts,
                max_days=1,
            )
        except AllocationError:
            return count
        count += 1


def build_day_plan(root: Path, requested_episodes: int | None = None) -> DayPlan:
    production = load_production(root)
    profile_name = production.effective_profile_name()
    profile = production.profile(profile_name)
    account_ids = [account.id for account in load_accounts(root).accounts]
    real_durations = _real_video_durations(root)
    average_clip = (
        sum(real_durations) / len(real_durations)
        if real_durations
        else float(production.video.default_duration_s)
    )
    average_episode = (profile.episode_seconds.min + profile.episode_seconds.max) / 2
    videos_per_episode = max(1, ceil(average_episode / average_clip))
    sample_durations = [
        (
            real_durations[index % len(real_durations)]
            if real_durations
            else production.video.default_duration_s
        )
        for index in range(videos_per_episode)
    ]
    costs = [
        production.video_credits(duration, resolution=profile.resolution)
        for duration in sample_durations
    ]
    expected_capacity = _one_day_episode_capacity(costs, account_ids, production, 1)
    worst_capacity = _one_day_episode_capacity(
        costs, account_ids, production, max(production.video.max_attempts, 1)
    )
    requested_expected = requested_worst = None
    if requested_episodes is not None:
        requested_items = [
            AllocationItem(f"requested-{episode}-{index}", cost)
            for episode in range(requested_episodes)
            for index, cost in enumerate(costs)
        ]
        for attempts, target in ((1, "expected"), (max(production.video.max_attempts, 1), "worst")):
            try:
                allocate(
                    requested_items,
                    account_ids,
                    production.accounts.daily_credits_per_account,
                    production.accounts.reserve_videos_per_account,
                    attempts,
                    max_days=1,
                )
                if target == "expected":
                    requested_expected = True
                else:
                    requested_worst = True
            except AllocationError:
                if target == "expected":
                    requested_expected = False
                else:
                    requested_worst = False
    return DayPlan(
        profile_name=profile_name,
        average_episode_seconds=average_episode,
        average_clip_seconds=average_clip,
        videos_per_episode=videos_per_episode,
        expected_episode_credits=sum(costs),
        worst_episode_credits=sum(cost * max(production.video.max_attempts, 1) for cost in costs),
        expected_episodes_per_day=expected_capacity,
        worst_episodes_per_day=worst_capacity,
        expected_videos_per_day=expected_capacity * videos_per_episode,
        worst_videos_per_day=worst_capacity * videos_per_episode,
        requested_episodes=requested_episodes,
        requested_expected_fits=requested_expected,
        requested_worst_fits=requested_worst,
    )
