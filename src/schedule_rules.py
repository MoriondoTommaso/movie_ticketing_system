"""Pure screening interval rules shared by scheduling and its tests."""

from datetime import datetime, time, timedelta

from src.database import ValidationError

OPENING = time(10, 0)
CLOSING = time(23, 59)


def validate_interval(starts_at: datetime, runtime_minutes: int) -> datetime:
    """Return the end of a valid screening, or raise ValidationError.

    Times are naive cinema-local (Europe/Rome) values with minute precision.
    The interval must start at or after 10:00 and end by 23:59 on the same date.
    """
    if (
        isinstance(runtime_minutes, bool)
        or not isinstance(runtime_minutes, int)
        or runtime_minutes <= 0
    ):
        raise ValidationError("Runtime must be a positive whole number of minutes")
    if not isinstance(starts_at, datetime) or starts_at.tzinfo is not None:
        raise ValidationError("Start must be a local date and time")
    if starts_at.second or starts_at.microsecond:
        raise ValidationError("Start must be a whole minute")
    if starts_at.time() < OPENING:
        raise ValidationError("Screenings cannot start before 10:00")
    ends_at = starts_at + timedelta(minutes=runtime_minutes)
    if ends_at > datetime.combine(starts_at.date(), CLOSING):
        raise ValidationError("Screenings must end by 23:59 on the same date")
    return ends_at


def overlaps(
    start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime
) -> bool:
    """Return whether half-open intervals [start, end) share any instant.

    Back-to-back screenings, where one ends exactly when the other starts, do not
    overlap; there is no cleaning interval.
    """
    return start_a < end_b and start_b < end_a
