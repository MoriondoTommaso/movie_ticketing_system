from datetime import UTC, date, datetime
from functools import partial
from unittest.mock import Mock

import pytest
from mysql.connector import OperationalError

from src import admin, screenings
from src.auth import Principal
from src.database import AuthorizationError, DatabaseError

ADMIN = Principal(1, "admin")


@pytest.mark.parametrize("operation", ["list_schedule", "list_capacity"])
def test_views_include_historical_screenings_and_remaining_seats(
    seeded_database, db_factory, operation
):
    with seeded_database.cursor() as cursor:
        cursor.execute(
            "UPDATE screenings SET starts_at='2000-01-01 10:00:00' WHERE screening_id=101"
        )
    seeded_database.commit()
    rows = getattr(screenings, operation)(ADMIN, connect=db_factory)
    assert [r.screening_id for r in rows] == [
        101,
        102,
        103,
        104,
        106,
        107,
        105,
        109,
        110,
        108,
        112,
        111,
    ]
    assert [r.available_seats for r in rows[:4]] == [1, 16, 0, 10]
    assert (rows[0].title, rows[0].theater_id, rows[0].starts_at, rows[0].language) == (
        "Fixture Movie 1",
        1,
        datetime(2000, 1, 1, 10),
        "English",
    )


@pytest.mark.parametrize("operation", ["list_schedule", "list_capacity"])
def test_views_filter_date_and_verify_stored_admin(
    seeded_database, db_factory, operation
):
    view = getattr(screenings, operation)
    assert view(ADMIN, screening_date=date(2000, 1, 1), connect=db_factory) == []
    assert [
        r.screening_id
        for r in view(
            ADMIN,
            screening_date=date(2026, 11, 24),
            connect=db_factory,
        )
    ] == [101, 102, 103]
    for principal in (Principal(11, "client"), Principal(11, "admin")):
        with pytest.raises(AuthorizationError):
            view(principal, connect=db_factory)


def test_views_wrap_driver_errors():
    for view in (screenings.list_schedule, screenings.list_capacity):
        with pytest.raises(DatabaseError, match="Screening database read failed"):
            view(ADMIN, connect=Mock(side_effect=OperationalError("driver details")))


def test_new_screening_has_all_seats_available_in_both_views(
    seeded_database, db_factory
):
    starts = datetime(2026, 11, 24, 11, 30)
    screening_id = screenings.create_screening(
        ADMIN,
        1,
        1,
        2,
        starts,
        connect=db_factory,
        clock=lambda: datetime(2026, 11, 23, 8, tzinfo=UTC),
    )
    for view in (screenings.list_schedule, screenings.list_capacity):
        rows = view(ADMIN, screening_date=starts.date(), connect=db_factory)
        assert rows[-1].screening_id == screening_id
        assert (rows[-1].available_seats, rows[-1].starts_at) == (10, starts)


def test_admin_menu_renders_both_views(
    seeded_database, db_factory, monkeypatch, capsys
):
    for name in ("list_schedule", "list_capacity"):
        monkeypatch.setattr(
            admin, name, partial(getattr(screenings, name), connect=db_factory)
        )
    inputs = iter(["2", "2026-11-24", "3", "2026-11-24", "2", "2000-01-01", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    admin.run(ADMIN)
    output = capsys.readouterr().out
    schedule, capacity = output.split("Remaining capacity", 1)
    for section in (schedule, capacity):
        assert "Fixture Movie 1" in section and "Theater 1" in section
        assert "2026-11-24 10:00" in section and "0 seats (advisory)" in section
    assert "No screenings found." in capacity
