from concurrent.futures import Future
from contextlib import ExitStack
from datetime import UTC, datetime
from threading import Event, Thread
from time import monotonic

from mysql.connector import Error, connect, errorcode

from src import booking
from src.auth import Principal
from src.database import CapacityError


def test_last_seat_contention(seeded_database, database_settings):
    settings = database_settings
    with ExitStack() as resources:
        active = {}

        def open_session():
            conn = connect(
                host=settings.host,
                port=settings.port,
                database=settings.name,
                user=settings.user,
                password=settings.password,
                autocommit=False,
                connection_timeout=3,
                read_timeout=4,
                write_timeout=4,
            )

            def close_idle_session():
                worker = active.get(id(conn))
                if worker is None or not worker.is_alive():
                    conn.close()

            resources.callback(close_idle_session)
            return conn

        _exercise_race(open_session, active)


def _exercise_race(open_session, active):
    admin = open_session()
    with admin.cursor() as cursor:
        cursor.execute(
            "SELECT t.capacity, s.sold_tickets, "
            "(SELECT SUM(quantity) FROM purchases WHERE screening_id=101) "
            "FROM screenings s JOIN theaters t USING(theater_id) WHERE screening_id=101"
        )
        assert cursor.fetchone() == (10, 9, 9)

    first_locked, release = Event(), Event()
    first, second = open_session(), open_session()
    assert first.connection_id != second.connection_id
    second_id = second.connection_id
    for conn in (first, second):
        with conn.cursor() as cursor:
            cursor.execute("SET SESSION innodb_lock_wait_timeout=3")

    def buy(conn, user, method):
        # Booking calls its injected clock only after the screening lock is held.
        def clock():
            if conn is first:
                first_locked.set()
                assert release.wait(8), "first booking was not released"
            return datetime(2026, 11, 23, 8, tzinfo=UTC)

        try:
            return booking.book_tickets(
                Principal(user, "client"),
                101,
                1,
                method,
                connect=lambda: conn,
                clock=clock,
            )
        except CapacityError as exc:
            return exc

    workers = []

    def start(conn, user, method):
        result = Future()

        def run():
            try:
                result.set_result(buy(conn, user, method))
            except BaseException as exc:
                result.set_exception(exc)

        worker = Thread(target=run, daemon=True)
        active[id(conn)] = worker
        workers.append((conn.connection_id, worker))
        worker.start()
        return result

    winner = start(first, 11, 201)
    try:
        assert first_locked.wait(3), "first booking did not pause holding the lock"
        loser = start(second, 12, 203)
        with admin.cursor(dictionary=True) as cursor:
            deadline = monotonic() + 2
            # Observe the actual server-side query, not merely a worker about to call it.
            while monotonic() < deadline:
                cursor.execute("SHOW FULL PROCESSLIST")
                if any(
                    row["Id"] == second_id and "FOR UPDATE OF s" in (row["Info"] or "")
                    for row in cursor.fetchall()
                ):
                    break
                assert not loser.done(), "contender completed before lock release"
                release.wait(0.02)
            else:
                raise AssertionError("contending locking read was not observed")
    finally:
        release.set()
        for _, worker in workers:
            worker.join(timeout=6)
        stuck = [
            (session_id, worker) for session_id, worker in workers if worker.is_alive()
        ]
        if stuck:
            try:
                with open_session().cursor() as cursor:
                    for session_id, _ in stuck:
                        try:
                            cursor.execute("KILL CONNECTION %s", (session_id,))
                        except Error as exc:
                            if exc.errno != errorcode.ER_NO_SUCH_THREAD:
                                raise
            finally:
                for _, worker in stuck:
                    worker.join(timeout=6)
            assert not any(worker.is_alive() for _, worker in stuck), (
                "booking worker hung after KILL"
            )
            raise AssertionError("booking worker required forced session cleanup")
    receipt = winner.result(timeout=0)
    assert isinstance(receipt, booking.BookingReceipt)
    assert isinstance(loser.result(timeout=0), CapacityError)

    assert not first.is_connected() and not second.is_connected()
    observer = open_session()
    with observer.cursor() as cursor:
        cursor.execute("SET SESSION innodb_lock_wait_timeout=1")
        cursor.execute(
            "SELECT sold_tickets FROM screenings WHERE screening_id=101 FOR UPDATE"
        )
        assert cursor.fetchone() == (10,)
        cursor.execute(
            "SELECT purchase_id,client_id,quantity FROM purchases WHERE screening_id=101 "
            "ORDER BY purchase_id"
        )
        assert cursor.fetchall() == [
            (301, 11, 5),
            (302, 12, 4),
            (receipt.purchase_id, 11, 1),
        ]
        cursor.execute(
            "SELECT active FROM payment_methods WHERE payment_method_id IN (201,203) FOR UPDATE"
        )
        assert cursor.fetchall() == [(1,), (1,)]
    observer.rollback()
