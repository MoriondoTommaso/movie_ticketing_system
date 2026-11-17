"""Authoritative, pure ticket pricing shared by search and booking."""

from calendar import monthrange
from datetime import date
from decimal import Decimal


def calculate_unit_price(
    release_date: date,
    screening_date: date,
    supports_3d: bool,
    enhanced_sound: bool,
) -> Decimal:
    """Price all surcharges before discounting, strictly after two calendar years.

    Dates are explicit cinema-local dates; no wall clock or display logic is used.
    A February 29 release has a February 28 anniversary in a non-leap year.
    """
    price = Decimal("15")
    if supports_3d:
        price += Decimal("5")
    if enhanced_sound:
        price += Decimal("3")
    years = screening_date.year - release_date.year
    anniversary_day = min(
        release_date.day, monthrange(screening_date.year, release_date.month)[1]
    )
    if years > 2 or (
        years == 2
        and (screening_date.month, screening_date.day)
        > (release_date.month, anniversary_day)
    ):
        price *= Decimal("0.80")
    return price.quantize(Decimal("0.01"))
