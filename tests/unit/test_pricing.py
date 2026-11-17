from datetime import date
from decimal import Decimal

import pytest

from src.pricing import calculate_unit_price


@pytest.mark.parametrize(
    ("supports_3d", "enhanced_sound", "expected"),
    [
        (False, False, "15.00"),
        (True, False, "20.00"),
        (False, True, "18.00"),
        (True, True, "23.00"),
    ],
)
def test_recent_movie_prices(supports_3d, enhanced_sound, expected):
    price = calculate_unit_price(
        date(2025, 6, 1), date(2026, 6, 1), supports_3d, enhanced_sound
    )

    assert isinstance(price, Decimal)
    assert price == Decimal(expected)
    assert price.as_tuple().exponent == -2


@pytest.mark.parametrize(
    ("supports_3d", "enhanced_sound", "expected"),
    [
        (False, False, "12.00"),
        (True, False, "16.00"),
        (False, True, "14.40"),
        (True, True, "18.40"),
    ],
)
def test_old_movie_discount_includes_all_surcharges(
    supports_3d, enhanced_sound, expected
):
    price = calculate_unit_price(
        date(2024, 6, 1), date(2026, 6, 2), supports_3d, enhanced_sound
    )

    assert price == Decimal(expected)
    assert price.as_tuple().exponent == -2


@pytest.mark.parametrize(
    ("release", "screening", "expected"),
    [
        (date(2024, 6, 1), date(2026, 5, 31), "23.00"),
        (date(2024, 6, 1), date(2026, 6, 1), "23.00"),
        (date(2024, 6, 1), date(2026, 6, 2), "18.40"),
        (date(2024, 2, 29), date(2026, 2, 27), "23.00"),
        (date(2024, 2, 29), date(2026, 2, 28), "23.00"),
        (date(2024, 2, 29), date(2026, 3, 1), "18.40"),
        (date(2022, 3, 1), date(2024, 2, 29), "23.00"),
        (date(2022, 3, 1), date(2024, 3, 1), "23.00"),
        (date(2022, 3, 1), date(2024, 3, 2), "18.40"),
    ],
)
def test_discount_starts_after_second_calendar_anniversary(
    release, screening, expected
):
    assert calculate_unit_price(release, screening, True, True) == Decimal(expected)
