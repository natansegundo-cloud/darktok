import pytest

from studio.allocator import (
    AllocationError,
    AllocationItem,
    allocate,
    capacity_for_clip,
    total_capacity_for_clip,
)


@pytest.mark.parametrize(
    ("cost", "expected"),
    [(5, 9), (6, 7), (7, 6)],
)
def test_capacity_uses_cost_and_reserve(cost: int, expected: int) -> None:
    assert capacity_for_clip(cost, daily_credits=50, reserve_videos=1) == expected
    assert total_capacity_for_clip(cost, 5, 50, 1) == expected * 5


def test_allocator_spreads_items_after_daily_capacity_is_used() -> None:
    items = [AllocationItem(f"P{index:02d}", 7) for index in range(7)]

    assignments = allocate(items, ["conta1", "conta2"], 50, 1, 1)

    assert len(assignments) == 7
    assert {item.account_id for item in assignments} == {"conta1", "conta2"}
    assert max(item.day for item in assignments) == 1


def test_allocator_reports_daily_overflow() -> None:
    items = [AllocationItem(f"P{index:02d}", 7) for index in range(13)]

    with pytest.raises(AllocationError, match="Capacidade diária insuficiente"):
        allocate(items, ["conta1", "conta2"], 50, 1, 1, max_days=1)


def test_worst_case_attempts_require_more_capacity_than_expected() -> None:
    items = [AllocationItem(f"P{index:02d}", 6) for index in range(9)]

    expected = allocate(items, ["conta1"], 50, 1, 1)
    worst = allocate(items, ["conta1"], 50, 1, 2)

    assert max(item.day for item in expected) == 2
    assert max(item.day for item in worst) == 3
    with pytest.raises(AllocationError):
        allocate(items, ["conta1"], 50, 1, 2, max_days=1)
