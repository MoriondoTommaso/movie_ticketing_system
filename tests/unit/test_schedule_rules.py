from datetime import UTC, date, datetime

import pytest

from src.database import ValidationError
from src.schedule_rules import overlaps, validate_interval


@pytest.mark.parametrize(
    ("starts_at", "runtime_minutes", "expected_end"),
    [
        (datetime(2026, 12, 1, 10, 0), 90, datetime(2026, 12, 1, 11, 30)),
        (datetime(2026, 12, 1, 22, 29), 90, datetime(2026, 12, 1, 23, 59)),
        (datetime(2026, 12, 1, 23, 58), 1, datetime(2026, 12, 1, 23, 59)),
    ],
)
def test_valid_interval_returns_exact_end(starts_at, runtime_minutes, expected_end):
    assert validate_interval(starts_at, runtime_minutes) == expected_end


@pytest.mark.parametrize(
    "starts_at",
    [
        datetime(2026, 12, 1, 9, 59),
        datetime(2026, 12, 1, 22, 30),
        datetime(2026, 12, 1, 23, 0),
    ],
)
def test_interval_outside_opening_hours_is_rejected(starts_at):
    with pytest.raises(ValidationError):
        validate_interval(starts_at, 90)


@pytest.mark.parametrize(
    "starts_at",
    [
        datetime(2026, 12, 1, 10, 0, 30),
        datetime(2026, 12, 1, 10, 0, 0, 1),
        datetime(2026, 12, 1, 10, 0, tzinfo=UTC),
        date(2026, 12, 1),
        "2026-12-01 10:00",
    ],
)
def test_start_must_be_naive_minute_precision_datetime(starts_at):
    with pytest.raises(ValidationError):
        validate_interval(starts_at, 90)


@pytest.mark.parametrize("runtime_minutes", [0, -1, True, 1.5, "90"])
def test_runtime_must_be_positive_int(runtime_minutes):
    with pytest.raises(ValidationError):
        validate_interval(datetime(2026, 12, 1, 10, 0), runtime_minutes)


def at(day, hour, minute):
    return datetime(2026, 12, day, hour, minute)


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ((at(1, 10, 0), at(1, 11, 30)), (at(1, 10, 0), at(1, 11, 30)), True),
        ((at(1, 10, 0), at(1, 11, 30)), (at(1, 10, 0), at(1, 12, 0)), True),
        ((at(1, 10, 0), at(1, 14, 0)), (at(1, 11, 0), at(1, 12, 30)), True),
        ((at(1, 10, 0), at(1, 11, 30)), (at(1, 11, 29), at(1, 12, 59)), True),
        ((at(1, 10, 0), at(1, 11, 30)), (at(1, 11, 30), at(1, 13, 0)), False),
        ((at(1, 10, 0), at(1, 11, 30)), (at(2, 10, 0), at(2, 11, 30)), False),
        ((at(1, 10, 0), at(1, 11, 30)), (at(1, 15, 0), at(1, 16, 30)), False),
    ],
    ids=[
        "identical",
        "equal-starts",
        "contained",
        "one-minute-overlap",
        "back-to-back",
        "adjacent-dates",
        "disjoint",
    ],
)
def test_overlaps_uses_half_open_intervals_symmetrically(a, b, expected):
    assert overlaps(*a, *b) is expected
    assert overlaps(*b, *a) is expected
