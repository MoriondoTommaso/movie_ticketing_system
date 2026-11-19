from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path

import pytest

from src import client, screenings
from src.auth import Principal
from src.database import (
    AuthorizationError,
    NotFoundError,
    RetryableDatabaseError,
    ValidationError,
)
from src.screenings import lock_screening, search_screenings

CLIENT = Principal(11, "client")


def demo_clock():
    return datetime(2026, 11, 23, 8, tzinfo=UTC)


def test_each_bound_filter_excludes_a_near_miss(seeded_database, db_factory):
    with seeded_database.cursor() as cursor:
        cursor.execute("INSERT INTO movie_genres (movie_id,genre_id) VALUES (2,2)")
        cursor.execute("DELETE FROM movie_genres WHERE movie_id = 2 AND genre_id = 1")
        cursor.execute("UPDATE movies SET title = 'Another title' WHERE movie_id = 3")
        cursor.executemany(
            "INSERT INTO screenings (screening_id,movie_id,theater_id,language_id,starts_at) "
            "VALUES (%s,%s,%s,%s,%s)",
            [
                (201, 1, 3, 2, "2026-11-24 11:00:00"),  # Upper endpoint.
                (202, 2, 3, 2, "2026-11-24 10:00:00"),  # Wrong genre.
                (203, 1, 3, 1, "2026-11-24 10:00:00"),  # Wrong language.
                (204, 1, 3, 2, "2026-11-25 10:00:00"),  # Wrong date.
                (205, 1, 3, 2, "2026-11-24 09:59:00"),  # Below range.
                (206, 1, 3, 2, "2026-11-24 11:01:00"),  # Above range.
                (207, 3, 3, 2, "2026-11-24 10:00:00"),  # Wrong title.
            ],
        )
    seeded_database.commit()
    filters = dict(
        title="Fixture Movie",
        genre_id=1,
        language_id=2,
        screening_date=date(2026, 11, 24),
        time_from=time(10),
        time_to=time(11),
    )
    rows = search_screenings(CLIENT, **filters, clock=demo_clock, connect=db_factory)
    artifact = Path(__file__).resolve().parents[2] / "queries.sql"
    title_pattern = f"%{filters.pop('title')}%"
    with seeded_database.cursor() as cursor:
        cursor.execute(
            artifact.read_text().split(";", 1)[0],
            dict(
                filters,
                title_pattern=title_pattern,
                now_local=datetime(2026, 11, 23, 9),
            ),
        )
        q1_ids = [row[0] for row in cursor.fetchall()]
    assert [row.screening_id for row in rows] == [101, 102, 201]
    assert q1_ids == [101, 102, 201]


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

    def genres(principal):
        return screenings.list_genres(principal, connect=db_factory)

    def languages(principal):
        return screenings.list_languages(principal, connect=db_factory)

    monkeypatch.setattr(client, "list_genres", genres, raising=False)
    monkeypatch.setattr(client, "list_languages", languages, raising=False)
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
    output = []

    def read(prompt):
        output.append(capsys.readouterr().out)
        if prompt.startswith("Genre ID"):
            assert "1: Drama" in output[-1] and "2: Comedy" in output[-1]
        if prompt.startswith("Language ID"):
            assert "1: Italian" in output[-1] and "2: English" in output[-1]
        return next(answers)

    monkeypatch.setattr("builtins.input", read)
    client.run(CLIENT)
    rendered = "".join([*output, capsys.readouterr().out])
    assert "Fixture Movie 1" in rendered and "EUR 20.00" in rendered
    assert "English" in rendered and "advisory" in rendered
    assert "No screenings found." in rendered


def test_catalog_checks_stored_roles_and_movie_language_membership(
    seeded_database, db_factory
):
    with seeded_database.cursor() as cursor:
        cursor.execute(
            "DELETE FROM movie_languages WHERE movie_id = 1 AND language_id = 1"
        )
    seeded_database.commit()

    admin = Principal(1, "admin")
    assert [
        item.name for item in screenings.list_genres(admin, connect=db_factory)
    ] == [
        "Drama",
        "Comedy",
    ]
    assert [
        item.name
        for item in screenings.list_languages(CLIENT, movie_id=1, connect=db_factory)
    ] == ["English"]
    with pytest.raises(NotFoundError):
        screenings.list_languages(admin, movie_id=99999, connect=db_factory)
    with pytest.raises(AuthorizationError):
        screenings.list_genres(Principal(11, "admin"), connect=db_factory)


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
