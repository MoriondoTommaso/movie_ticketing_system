from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from mysql.connector import OperationalError, errorcode

from src.auth import Principal
from src.booking import book_tickets
from src.database import CapacityError, DatabaseError, RetryableDatabaseError


@pytest.mark.parametrize("write_fails", [True, False])
def test_write_cursor_close_failure(
    seeded_database, db_factory, monkeypatch, write_fails
):
    conn = db_factory()
    original = conn.cursor

    def factory(*args, **kwargs):
        cursor = original(*args, **kwargs)
        execute, close = cursor.execute, cursor.close

        def fail_close():
            close()
            raise OperationalError("Injected cursor close failure")

        def inject(sql, params=None):
            execute(sql, params)
            if sql.startswith("INSERT INTO purchases"):
                monkeypatch.setattr(cursor, "close", fail_close)
                if write_fails:
                    raise OperationalError(
                        "Injected deadlock", errno=errorcode.ER_LOCK_DEADLOCK
                    )

        monkeypatch.setattr(cursor, "execute", inject)
        return cursor

    monkeypatch.setattr(conn, "cursor", factory)
    expected = RetryableDatabaseError if write_fails else DatabaseError
    with pytest.raises(expected) as failure:
        _book(lambda: conn)
    assert type(failure.value) is expected
    assert not conn.is_connected()
    assert _state(db_factory()) == (9, 2)


def _book(connect):
    return book_tickets(
        Principal(11, "client"),
        101,
        1,
        201,
        connect=connect,
        clock=lambda: datetime(2026, 11, 23, 8, tzinfo=UTC),
    )


def _state(conn):
    with conn.cursor() as cursor:
        return _state_on_cursor(cursor)


@pytest.mark.parametrize(
    ("statement", "sold", "errno", "expected"),
    [
        ("INSERT INTO purchases", 9, None, DatabaseError),
        ("UPDATE screenings", 10, None, DatabaseError),
        (
            "INSERT INTO purchases",
            9,
            errorcode.ER_LOCK_DEADLOCK,
            RetryableDatabaseError,
        ),
    ],
)
def test_failed_write_rolls_back_and_releases_locks(
    seeded_database, db_factory, monkeypatch, statement, sold, errno, expected
):
    conn = db_factory()
    original = conn.cursor
    rollback = Mock(wraps=conn.rollback)
    injected = Mock()
    cursors = []

    def cursor_factory(*args, **kwargs):
        cursor = original(*args, **kwargs)
        execute = cursor.execute
        close = Mock(wraps=cursor.close)
        cursors.append(close)

        def execute_then_fail(sql, params=None):
            execute(sql, params)
            if sql.startswith(statement):
                assert _state_on_cursor(cursor) == (sold, 3)
                injected()
                raise OperationalError("Injected write failure", errno=errno)

        monkeypatch.setattr(cursor, "execute", execute_then_fail)
        monkeypatch.setattr(cursor, "close", close)
        return cursor

    monkeypatch.setattr(conn, "cursor", cursor_factory)
    monkeypatch.setattr(conn, "rollback", rollback)
    connect = Mock(return_value=conn)
    with pytest.raises(expected) as failure:
        _book(connect)
    assert type(failure.value) is expected
    connect.assert_called_once()
    injected.assert_called_once()
    rollback.assert_called_once()
    for close in cursors:
        close.assert_called_once()
    assert not conn.is_connected()
    assert _state(db_factory()) == (9, 2)
    retry = db_factory()
    with retry.cursor() as cursor:
        cursor.execute("SET SESSION innodb_lock_wait_timeout=1")
    assert _book(lambda: retry).quantity == 1
    assert _state(db_factory()) == (10, 3)


def _state_on_cursor(cursor):
    cursor.execute(
        "SELECT sold_tickets, (SELECT COUNT(*) FROM purchases WHERE screening_id=101) "
        "FROM screenings WHERE screening_id=101"
    )
    return cursor.fetchone()


def test_lost_commit_acknowledgement_is_not_retryable(
    seeded_database, db_factory, monkeypatch
):
    conn = db_factory()
    commit = conn.commit

    def commit_without_ack():
        commit()
        raise OperationalError("Lost acknowledgement", errno=2013)

    monkeypatch.setattr(conn, "commit", commit_without_ack)
    rollback = Mock(side_effect=OperationalError("Lost connection during rollback"))
    monkeypatch.setattr(conn, "rollback", rollback)
    connect = Mock(return_value=conn)
    with pytest.raises(DatabaseError, match="outcome is unknown") as failure:
        _book(connect)
    connect.assert_called_once()
    rollback.assert_called_once()
    assert not isinstance(failure.value, RetryableDatabaseError)
    assert not conn.is_connected()
    assert _state(db_factory()) == (10, 3)


def test_real_payment_lock_timeout_releases_the_screening(seeded_database, db_factory):
    owner, contender = db_factory(), db_factory()
    with owner.cursor() as cursor:
        cursor.execute(
            "SELECT active FROM payment_methods WHERE payment_method_id=201 FOR UPDATE"
        )
        cursor.fetchall()
    with contender.cursor() as cursor:
        cursor.execute("SET SESSION innodb_lock_wait_timeout=1")
    connect = Mock(return_value=contender)
    with pytest.raises(RetryableDatabaseError):
        _book(connect)
    connect.assert_called_once()
    assert not contender.is_connected()
    assert _state(db_factory()) == (9, 2)
    owner.rollback()
    retry = db_factory()
    with retry.cursor() as cursor:
        cursor.execute("SET SESSION innodb_lock_wait_timeout=1")
    assert _book(lambda: retry).quantity == 1
    assert _state(db_factory()) == (10, 3)


def test_server_rejected_commit_rolls_back_without_retry(
    seeded_database, db_factory, monkeypatch
):
    conn = db_factory()
    commit = Mock(
        side_effect=OperationalError("Deadlock", errno=errorcode.ER_LOCK_DEADLOCK)
    )
    rollback = Mock(wraps=conn.rollback)
    monkeypatch.setattr(conn, "commit", commit)
    monkeypatch.setattr(conn, "rollback", rollback)
    connect = Mock(return_value=conn)
    with pytest.raises(RetryableDatabaseError):
        _book(connect)
    connect.assert_called_once()
    commit.assert_called_once()
    rollback.assert_called_once()
    assert not conn.is_connected()
    assert _state(db_factory()) == (9, 2)


def test_close_error_after_commit_keeps_receipt(
    seeded_database, db_factory, monkeypatch
):
    conn = db_factory()
    close = conn.close

    def close_then_fail():
        close()
        raise OperationalError("Close failed after commit")

    monkeypatch.setattr(conn, "close", close_then_fail)
    connect = Mock(return_value=conn)
    receipt = _book(connect)
    connect.assert_called_once()
    assert not conn.is_connected()
    observer = db_factory()
    assert _state(observer) == (10, 3)
    with observer.cursor() as cursor:
        cursor.execute(
            "SELECT quantity FROM purchases WHERE purchase_id=%s",
            (receipt.purchase_id,),
        )
        assert cursor.fetchone() == (1,)


def test_validation_closes_cursor_and_connection(
    seeded_database, db_factory, monkeypatch
):
    conn = db_factory()
    original = conn.cursor
    closes = []

    def cursor_factory(*args, **kwargs):
        cursor = original(*args, **kwargs)
        close = Mock(wraps=cursor.close)
        closes.append(close)
        monkeypatch.setattr(cursor, "close", close)
        return cursor

    monkeypatch.setattr(conn, "cursor", cursor_factory)
    rollback = Mock(wraps=conn.rollback)
    monkeypatch.setattr(conn, "rollback", rollback)
    with pytest.raises(CapacityError):
        book_tickets(
            Principal(11, "client"),
            101,
            2,
            201,
            connect=lambda: conn,
            clock=lambda: datetime(2026, 11, 23, 8, tzinfo=UTC),
        )
    assert closes
    for close in closes:
        close.assert_called_once()
    rollback.assert_called_once()
    assert not conn.is_connected()
    assert _state(db_factory()) == (9, 2)
