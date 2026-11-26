from concurrent.futures import Future
from datetime import UTC, datetime
from threading import Event, Thread
from time import monotonic

import pytest
from mysql.connector import connect

from src.auth import Principal
from src.database import ValidationError
from src.screenings import create_screening


@pytest.mark.parametrize(
    ("theater", "minute", "overlaps"), [(1, 30, True), (1, 90, False), (2, 30, False)]
)
def test_schedule_race(seeded_database, database_settings, theater, minute, overlaps):
    settings = database_settings

    def session():
        return connect(
            host=settings.host,
            port=settings.port,
            database=settings.name,
            user=settings.user,
            password=settings.password,
            autocommit=False,
            connection_timeout=3,
            read_timeout=5,
            write_timeout=5,
        )

    def participant():
        conn = session()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ"
                )
                cursor.execute("SELECT @@session.transaction_isolation")
                assert cursor.fetchone() == ("REPEATABLE-READ",)
                cursor.execute("SET SESSION innodb_lock_wait_timeout=4")
            return conn
        except BaseException:
            conn.close()
            raise

    now = datetime(2026, 11, 23, 8, tzinfo=UTC)
    start = datetime(2026, 12, 1, 10)
    contender_start = start.replace(hour=10 + minute // 60, minute=minute % 60)
    admin = Principal(1, "admin")
    ready, result = Event(), Future()
    worker_id = None

    def contend():
        nonlocal worker_id
        try:
            with participant() as conn:
                worker_id = conn.connection_id
                ready.set()
                screening_id = create_screening(
                    admin,
                    1,
                    theater,
                    2,
                    contender_start,
                    clock=lambda: now,
                    connect=lambda: conn,
                )
            result.set_result(screening_id)
        except BaseException as exc:
            result.set_exception(exc)
            ready.set()

    worker = Thread(target=contend, daemon=True)

    def winner_clock():
        worker.start()
        assert ready.wait(4), "contender did not connect"
        if theater != 1:
            result.result(timeout=4)
            return now
        deadline = monotonic() + 3
        with session() as observer, observer.cursor() as cursor:
            while monotonic() < deadline and not result.done():
                cursor.execute("SHOW FULL PROCESSLIST")
                if any(
                    row[0] == worker_id
                    and row[7]
                    and "FROM theaters WHERE theater_id = 1 FOR UPDATE" in row[7]
                    for row in cursor.fetchall()
                ):
                    return now
        pytest.fail("contender did not reach the theater lock while winner held it")

    try:
        winner = create_screening(
            admin, 1, 1, 2, start, clock=winner_clock, connect=participant
        )
    finally:
        if worker.ident is not None:
            worker.join(7)
            if worker.is_alive():
                assert worker_id is not None, "contender did not connect or stop"
                with session() as observer, observer.cursor() as cursor:
                    cursor.execute("KILL CONNECTION %s", (worker_id,))
                worker.join(7)
                assert not worker.is_alive(), "contender survived session termination"
                pytest.fail("contender required forced cleanup")

    expected = {winner}
    if overlaps:
        with pytest.raises(ValidationError, match="overlaps"):
            result.result()
    else:
        expected.add(result.result())
    with session() as conn, conn.cursor() as cursor:
        cursor.execute(
            "SELECT screening_id, theater_id, starts_at FROM screenings WHERE starts_at >= %s",
            (start,),
        )
        rows = {(winner, 1, start)}
        if not overlaps:
            rows.add((result.result(), theater, contender_start))
        assert set(cursor.fetchall()) == rows
    assert (
        create_screening(
            admin, 1, 1, 2, start.replace(hour=14), clock=lambda: now, connect=session
        )
        not in expected
    )
