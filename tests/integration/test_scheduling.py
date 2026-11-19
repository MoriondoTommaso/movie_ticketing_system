from datetime import UTC, datetime

import pytest

from src import admin, screenings
from src.auth import Principal
from src.database import (
    AuthorizationError,
    NotFoundError,
    RetryableDatabaseError,
    ValidationError,
)

ADMIN = Principal(1, "admin")


def clock():
    return datetime(2026, 11, 23, 8, tzinfo=UTC)


def create(db_factory, start, *, movie=1, theater=1, language=2, principal=ADMIN):
    return screenings.create_screening(
        principal, movie, theater, language, start, connect=db_factory, clock=clock
    )


def test_create_persists_back_to_back_screenings(seeded_database, db_factory):
    starts = [datetime(2026, 11, 24, 11, 30), datetime(2026, 11, 24, 13)]
    ids = [create(db_factory, start) for start in starts]
    with db_factory().cursor() as cursor:
        cursor.execute(
            "SELECT starts_at,sold_tickets FROM screenings WHERE screening_id IN (%s,%s) "
            "ORDER BY starts_at",
            tuple(ids),
        )
        assert cursor.fetchall() == [(start, 0) for start in starts]


@pytest.mark.parametrize(
    ("start", "options", "error"),
    [
        (datetime(2026, 11, 24, 11, 30), {"movie": 999}, NotFoundError),
        (datetime(2026, 11, 24, 11, 30), {"theater": 999}, NotFoundError),
        (datetime(2026, 11, 24, 11, 30), {"language": 999}, ValidationError),
        (datetime(2026, 11, 24, 11, 29), {}, ValidationError),
        (datetime(2026, 11, 24, 23), {}, ValidationError),
        (datetime(2026, 11, 22, 10), {}, ValidationError),
        (datetime(2026, 11, 24, 12, 0, 1), {}, ValidationError),
        (
            datetime(2026, 11, 24, 11, 30),
            {"principal": Principal(11, "client")},
            AuthorizationError,
        ),
        (
            datetime(2026, 11, 24, 11, 30),
            {"principal": Principal(11, "admin")},
            AuthorizationError,
        ),
    ],
)
def test_invalid_creation_does_not_insert(
    seeded_database, db_factory, start, options, error
):
    with pytest.raises(error):
        create(db_factory, start, **options)
    with db_factory().cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM screenings")
        assert cursor.fetchone() == (12,)


def test_cli_shows_create_action(monkeypatch):
    def read(prompt):
        assert "1. Add screening" in prompt
        return "0"

    monkeypatch.setattr("builtins.input", read)
    admin.run(ADMIN)


def test_overlap_read_sees_commit_after_snapshot(
    seeded_database, db_factory, monkeypatch
):
    conn = db_factory()
    begin = conn.start_transaction
    starts = datetime(2026, 11, 24, 15)

    def begin_with_stale_snapshot():
        begin(consistent_snapshot=True)
        create(db_factory, starts)

    monkeypatch.setattr(conn, "start_transaction", begin_with_stale_snapshot)
    with pytest.raises(ValidationError, match="overlaps"):
        create(lambda: conn, starts)
    assert not conn.is_connected()
    with db_factory().cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM screenings WHERE theater_id=1 AND starts_at=%s",
            (starts,),
        )
        assert cursor.fetchone() == (1,)


def test_theater_lock_failure_closes_connection_before_clock(
    seeded_database, db_factory
):
    owner, contender = db_factory(), db_factory()
    with owner.cursor() as cursor:
        cursor.execute("SELECT theater_id FROM theaters WHERE theater_id=1 FOR UPDATE")
        cursor.fetchall()
    with contender.cursor() as cursor:
        cursor.execute("SET SESSION innodb_lock_wait_timeout=1")
    with pytest.raises(RetryableDatabaseError):
        screenings.create_screening(
            ADMIN,
            1,
            1,
            2,
            datetime(2026, 11, 24, 15),
            connect=lambda: contender,
            clock=lambda: pytest.fail("Clock before theater lock"),
        )
    assert not contender.is_connected()
    owner.rollback()
    assert create(db_factory, datetime(2026, 11, 24, 15)) > 0
