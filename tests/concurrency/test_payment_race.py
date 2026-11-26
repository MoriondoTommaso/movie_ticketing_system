from concurrent.futures import Future
from contextlib import ExitStack
from datetime import UTC, datetime
from threading import Event, Thread
from time import monotonic

import pytest
from mysql.connector import Error, connect, errorcode

from src import booking, payments
from src.auth import Principal
from src.database import ValidationError


@pytest.mark.parametrize("booking_first", [True, False])
def test_payment_race(seeded_database, database_settings, monkeypatch, booking_first):
    s = database_settings

    def session():
        return connect(
            host=s.host,
            port=s.port,
            database=s.name,
            user=s.user,
            password=s.password,
            connection_timeout=3,
            read_timeout=5,
            write_timeout=5,
        )

    buyer = Principal(11, "client")

    def clock():
        return datetime(2026, 11, 23, 8, tzinfo=UTC)

    held, release = Event(), Event()
    original = payments._lock_owned_method
    lock_screening = booking.lock_screening

    workers = []
    with ExitStack() as stack:
        observer = stack.enter_context(session())

        def participant():
            conn = session()
            session_id = conn.connection_id

            def close_if_idle():
                if not any(
                    key == session_id and worker.is_alive() for key, worker in workers
                ):
                    conn.close()

            stack.callback(close_if_idle)
            return conn

        first, second = participant(), participant()
        assert first.connection_id != second.connection_id
        second_id = second.connection_id
        booking_conn = first if booking_first else second
        screening_held = Event()

        def lock_seats(conn, screening_id):
            screening = lock_screening(conn, screening_id)
            if conn is booking_conn:
                screening_held.set()
            return screening

        def lock(conn, principal, method_id):
            if conn is booking_conn:
                assert screening_held.is_set(), "booking must lock screening first"
            method = original(conn, principal, method_id)
            if conn is first:
                held.set()
                assert release.wait(8), "payment lock holder not released"
            return method

        monkeypatch.setattr(payments, "_lock_owned_method", lock)
        monkeypatch.setattr(booking, "lock_screening", lock_seats)

        def start(conn, buy):
            result = Future()

            def run():
                try:
                    if buy:
                        result.set_result(
                            booking.book_tickets(
                                buyer, 101, 1, 201, connect=lambda: conn, clock=clock
                            )
                        )
                    else:
                        result.set_result(
                            payments.deactivate_method(buyer, 201, connect=lambda: conn)
                        )
                except BaseException as exc:
                    result.set_exception(exc)

            worker = Thread(target=run, daemon=True)
            workers.append((conn.connection_id, worker))
            worker.start()
            return result

        try:
            winner = start(first, booking_first)
            assert held.wait(4), "first operation did not acquire payment lock"
            loser = start(second, not booking_first)
            deadline = monotonic() + 3
            with observer.cursor() as cursor:
                while monotonic() < deadline and not loser.done():
                    cursor.execute("SHOW FULL PROCESSLIST")
                    if any(
                        r[0] == second_id
                        and r[7]
                        and "FROM payment_methods" in r[7]
                        and "FOR UPDATE" in r[7]
                        for r in cursor.fetchall()
                    ):
                        break
                else:
                    pytest.fail("contender did not reach the held payment lock")
        finally:
            release.set()
            forced = []
            for session_id, worker in workers:
                worker.join(7)
                if worker.is_alive():
                    termination_error = None
                    try:
                        with observer.cursor() as cursor:
                            cursor.execute("KILL CONNECTION %s", (session_id,))
                    except Error as exc:
                        termination_error = exc
                    finally:
                        worker.join(7)
                    alive = worker.is_alive()
                    if (
                        termination_error is not None
                        and termination_error.errno == errorcode.ER_NO_SUCH_THREAD
                        and not alive
                    ):
                        continue
                    forced.append((session_id, alive, termination_error))
            assert not forced, f"forced cleanup (session, still alive, error): {forced}"

        receipt = winner.result()
        if booking_first:
            assert loser.result() is None
        else:
            with pytest.raises(ValidationError, match="Invalid payment method"):
                loser.result()
        with observer.cursor() as cursor:
            cursor.execute(
                "SELECT active FROM payment_methods WHERE payment_method_id=201"
            )
            assert cursor.fetchone() == (0,)
            cursor.execute("SELECT sold_tickets FROM screenings WHERE screening_id=101")
            assert cursor.fetchone() == (9 + booking_first,)
            cursor.execute(
                "SELECT purchase_id, payment_method_id, quantity FROM purchases "
                "WHERE screening_id=101 ORDER BY purchase_id"
            )
            expected = [(301, 202, 5), (302, 203, 4)]
            if booking_first:
                expected.append((receipt.purchase_id, 201, 1))
            assert cursor.fetchall() == expected
        with observer.cursor() as cursor:
            cursor.execute(
                "SELECT screening_id FROM screenings WHERE screening_id=101 FOR UPDATE NOWAIT"
            )
            assert cursor.fetchone() == (101,)
            cursor.execute(
                "SELECT payment_method_id FROM payment_methods WHERE payment_method_id=201 FOR UPDATE NOWAIT"
            )
            assert cursor.fetchone() == (201,)


def test_foreign_payment_remains_rejected(seeded_database, db_factory):
    buyer = Principal(11, "client")
    with pytest.raises(ValidationError, match="Invalid payment method"):
        booking.book_tickets(
            buyer,
            101,
            1,
            203,
            connect=db_factory,
            clock=lambda: datetime(2026, 11, 23, 8, tzinfo=UTC),
        )
    with pytest.raises(ValidationError, match="Invalid payment method"):
        payments.deactivate_method(buyer, 203, connect=db_factory)
