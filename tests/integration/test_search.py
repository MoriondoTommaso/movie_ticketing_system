from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path

import pytest

from src import client
from src.auth import Principal
from src.database import NotFoundError, RetryableDatabaseError, ValidationError
from src.screenings import lock_screening, search_screenings

CLIENT = Principal(11, "client")


def demo_clock():
    return datetime(2026, 11, 23, 8, tzinfo=UTC)


def test_q1_artifact_matches_search(seeded_database, db_factory):
    artifact = Path(__file__).resolve().parents[2] / "queries.sql"
    with seeded_database.cursor() as cursor:
        cursor.execute(
            artifact.read_text().split(";", 1)[0],
            dict(
                title_pattern="%Movie%",
                genre_id=1,
                language_id=2,
                screening_date=None,
                time_from=time(10),
                time_to=time(10),
                now_local=datetime(2026, 11, 23, 9),
            ),
        )
        actual = cursor.fetchall()
    rows = search_screenings(
        CLIENT,
        title="Movie",
        genre_id=1,
        language_id=2,
        time_from=time(10),
        time_to=time(10),
        clock=demo_clock,
        connect=db_factory,
    )
    assert [tuple(vars(r).values()) for r in rows] == actual


def test_cli_search_and_empty_result(seeded_database, db_factory, monkeypatch, capsys):
    def search(principal, **filters):
        return search_screenings(
            principal, **filters, clock=demo_clock, connect=db_factory
        )

    monkeypatch.setattr(client, "search_screenings", search, raising=False)
    answers = iter(
        [
            "2",
            "Movie 1",
            "1",
            "2",
            "2026-11-24",
            "10:00",
            "10:00",
            "2",
            "Missing title",
            "",
            "",
            "",
            "",
            "",
            "0",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    client.run(CLIENT)
    output = capsys.readouterr().out
    assert "Fixture Movie 1" in output and "EUR 20.00" in output
    assert "English" in output and "advisory" in output
    assert "No screenings found." in output


def test_combined_search_returns_each_screening_once(seeded_database, db_factory):
    rows = search_screenings(
        CLIENT,
        title="Movie 1",
        genre_id=1,
        language_id=2,
        screening_date=date(2026, 11, 24),
        time_from=time(10),
        time_to=time(10),
        clock=demo_clock,
        connect=db_factory,
    )
    assert [(r.screening_id, r.unit_price, r.available_seats) for r in rows] == [
        (101, Decimal("15.00"), 1),
        (102, Decimal("20.00"), 16),
    ]
    assert [(r.theater_id, r.supports_3d, r.enhanced_sound) for r in rows] == [
        (1, False, False),
        (2, True, False),
    ]
    assert all(r.title == "Fixture Movie 1" and r.language == "English" for r in rows)


@pytest.mark.parametrize("title", ["%", "_", "!", "not a title"])
def test_title_is_literal(seeded_database, db_factory, title):
    assert (
        search_screenings(CLIENT, title=title, clock=demo_clock, connect=db_factory)
        == []
    )


def test_started_results_use_local_time(seeded_database, db_factory):
    rows = search_screenings(
        CLIENT,
        clock=lambda: datetime(2026, 11, 24, 9, tzinfo=UTC),
        connect=db_factory,
    )
    assert [r.screening_id for r in rows] == [
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


def test_reversed_range_is_rejected_before_query():
    with pytest.raises(ValidationError):
        search_screenings(CLIENT, time_from=time(11), time_to=time(10))


def test_booking_lookup_uses_current_read_and_locks_until_rollback(
    seeded_database, db_factory
):
    caller, writer = db_factory(), db_factory()
    caller.start_transaction()
    with caller.cursor() as cursor:
        cursor.execute("SELECT sold_tickets FROM screenings WHERE screening_id = 101")
        assert cursor.fetchone() == (9,)
    with writer.cursor() as cursor:
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 1")
        cursor.execute(
            "UPDATE screenings SET sold_tickets = 10 WHERE screening_id = 101"
        )
    writer.commit()
    assert lock_screening(caller, 101).sold_tickets == 10
    with pytest.raises(RetryableDatabaseError):
        lock_screening(writer, 101)
    writer.rollback()
    caller.rollback()
    assert lock_screening(writer, 101).sold_tickets == 10


def test_booking_lookup_preserves_transaction(seeded_database, db_factory):
    conn = db_factory()
    conn.start_transaction()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE screenings SET sold_tickets=10 WHERE screening_id=101")
    row = lock_screening(conn, 101)
    assert (row.capacity, row.sold_tickets, row.runtime_minutes) == (10, 10, 90)
    with pytest.raises(NotFoundError):
        lock_screening(conn, 99999)
    assert conn.in_transaction
    conn.rollback()
    assert (
        search_screenings(CLIENT, clock=demo_clock, connect=db_factory)[
            0
        ].available_seats
        == 1
    )
