from __future__ import annotations

from dataclasses import dataclass
from math import floor


class AllocationError(ValueError):
    """Raised when the configured accounts cannot reserve a video."""


@dataclass(frozen=True)
class AllocationItem:
    shot_id: str
    cost: int


@dataclass(frozen=True)
class Assignment:
    shot_id: str
    account_id: str
    day: int


@dataclass
class _AccountState:
    account_id: str
    credits_used: int = 0
    video_count: int = 0


def capacity_for_clip(cost: int, daily_credits: int, reserve_videos: int) -> int:
    if cost <= 0:
        raise AllocationError("O custo do clipe precisa ser maior que zero.")
    return max(floor(daily_credits / cost) - reserve_videos, 0)


def total_capacity_for_clip(
    cost: int,
    account_count: int,
    daily_credits: int,
    reserve_videos: int,
) -> int:
    return account_count * capacity_for_clip(cost, daily_credits, reserve_videos)


def allocate(
    items: list[AllocationItem],
    account_ids: list[str],
    daily_credits: int,
    reserve_videos: int,
    attempts: int,
    *,
    max_days: int | None = None,
) -> list[Assignment]:
    if not account_ids:
        raise AllocationError("Nenhuma conta foi encontrada em config/accounts.yaml.")
    if attempts < 1:
        raise AllocationError("video.max_attempts precisa ser maior que zero.")

    days: list[dict[str, _AccountState]] = []
    assignments: list[Assignment] = []

    def new_day() -> dict[str, _AccountState]:
        return {account_id: _AccountState(account_id) for account_id in account_ids}

    for item in items:
        if capacity_for_clip(item.cost, daily_credits, reserve_videos) == 0:
            raise AllocationError(
                f"Nenhuma conta consegue reservar o clipe {item.shot_id} com custo "
                f"{item.cost} créditos mantendo a reserva configurada."
            )
        assigned = False
        for day_index, states in enumerate(days, start=1):
            candidates = [
                state
                for state in states.values()
                if state.video_count < capacity_for_clip(
                    item.cost, daily_credits, reserve_videos
                )
                and state.credits_used + item.cost * attempts <= daily_credits
            ]
            if not candidates:
                continue
            candidate = sorted(
                candidates,
                key=lambda state: (
                    -(state.video_count > 0),
                    state.credits_used,
                    state.account_id,
                ),
            )[0]
            candidate.credits_used += item.cost * attempts
            candidate.video_count += 1
            assignments.append(Assignment(item.shot_id, candidate.account_id, day_index))
            assigned = True
            break

        if assigned:
            continue
        if max_days is not None and len(days) >= max_days:
            raise AllocationError(
                f"Capacidade diária insuficiente para reservar o clipe {item.shot_id}."
            )
        states = new_day()
        days.append(states)
        candidate = states[account_ids[0]]
        if candidate.credits_used + item.cost * attempts > daily_credits:
            raise AllocationError(
                f"O clipe {item.shot_id} excede os créditos diários de uma conta."
            )
        candidate.credits_used += item.cost * attempts
        candidate.video_count += 1
        assignments.append(Assignment(item.shot_id, candidate.account_id, len(days)))

    return assignments
