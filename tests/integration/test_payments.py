from functools import partial

import pytest
from mysql.connector import OperationalError

from src import client, payments
from src.auth import Principal
from src.database import (
    AuthorizationError,
    DatabaseError,
    RetryableDatabaseError,
    ValidationError,
)
from src.payments import add_method, list_methods, lock_valid_method

CLIENT = Principal(11, "client")


def test_lists_owned_methods_including_inactive(seeded_database, db_factory):
    rows = list_methods(CLIENT, connect=db_factory)
    assert [(r.payment_method_id, r.active) for r in rows] == [
        (201, True),
        (202, False),
    ]
    assert rows[0].masked_number.endswith("0201")
    assert sum(c.isdigit() for c in rows[0].masked_number) == 4
    assert all(r.client_id == 11 for r in rows)


@pytest.mark.parametrize(
    ("kind", "number"), [("credit", "0" * 9 + "-1234"), ("debit", "0" * 15 + " 1234")]
)
def test_add_commits_normalized_synthetic_method(
    seeded_database, db_factory, kind, number
):
    address = "O'Neil; -- Demo Lane"
    added = add_method(CLIENT, kind, number, f" {address} ", connect=db_factory)
    assert added in list_methods(CLIENT, connect=db_factory)
    assert added.active and added.payment_type == kind
    assert added.billing_address == address
    with db_factory().cursor() as cursor:
        cursor.execute(
            "SELECT card_number FROM payment_methods WHERE payment_method_id=%s",
            (added.payment_method_id,),
        )
        assert cursor.fetchone() == (number.replace("-", "").replace(" ", ""),)
    assert len(list_methods(Principal(12, "client"), connect=db_factory)) == 1


@pytest.mark.parametrize(
    "principal", [None, Principal(1, "admin"), Principal(1, "client")]
)
def test_public_services_reject_unauthorized_principals(
    seeded_database, db_factory, principal
):
    with pytest.raises(AuthorizationError):
        list_methods(principal, connect=db_factory)
    with pytest.raises(AuthorizationError):
        add_method(principal, "credit", "0" * 13, "Demo Lane", connect=db_factory)


@pytest.mark.parametrize("method_id", [202, 203, 99999, True, 0, "201"])
def test_lookup_denies_invalid_inactive_foreign_and_missing(seeded_database, method_id):
    with pytest.raises(ValidationError, match="^Invalid payment method$"):
        lock_valid_method(seeded_database, CLIENT, method_id)


def test_lookup_holds_row_lock_until_caller_rolls_back(seeded_database, db_factory):
    owner, contender = db_factory(), db_factory()
    owner.start_transaction()
    method = lock_valid_method(owner, CLIENT, 201)
    assert (method.payment_method_id, method.client_id, method.active) == (
        201,
        11,
        True,
    )
    with contender.cursor() as cursor:
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 1")
    contender.start_transaction()
    with pytest.raises(RetryableDatabaseError):
        lock_valid_method(contender, CLIENT, 201)
    assert contender.in_transaction
    contender.rollback()
    owner.rollback()
    contender.start_transaction()
    assert lock_valid_method(contender, CLIENT, 201) == method


def test_deactivation_keeps_history_and_is_idempotent(seeded_database, db_factory):
    for _ in range(2):
        assert payments.deactivate_method(CLIENT, 201, connect=db_factory) is None
    assert [
        (m.payment_method_id, m.active)
        for m in list_methods(CLIENT, connect=db_factory)
    ] == [(201, False), (202, False)]
    with db_factory().cursor() as cursor:
        cursor.execute(
            "SELECT purchase_id FROM purchases WHERE payment_method_id = %s "
            "ORDER BY purchase_id",
            (201,),
        )
        assert cursor.fetchall() == [(303,), (308,)]
    with pytest.raises(ValidationError, match="^Invalid payment method$"):
        lock_valid_method(db_factory(), CLIENT, 201)


@pytest.mark.parametrize("method_id", [203, 99999, True])
def test_deactivation_denies_non_owned_or_invalid_id(
    seeded_database, db_factory, method_id
):
    conn = db_factory()
    with pytest.raises(ValidationError, match="^Invalid payment method$"):
        payments.deactivate_method(CLIENT, method_id, connect=lambda: conn)
    if method_id is not True:
        assert not conn.is_connected()
    assert list_methods(Principal(12, "client"), connect=db_factory)[0].active


def test_deactivation_timeout_closes_connection_and_can_retry(
    seeded_database, db_factory
):
    owner, contender = db_factory(), db_factory()
    owner.start_transaction()
    lock_valid_method(owner, CLIENT, 201)
    with contender.cursor() as cursor:
        cursor.execute("SET SESSION innodb_lock_wait_timeout = 1")
    with pytest.raises(RetryableDatabaseError):
        payments.deactivate_method(CLIENT, 201, connect=lambda: contender)
    assert not contender.is_connected()
    owner.rollback()
    assert list_methods(CLIENT, connect=db_factory)[0].active
    payments.deactivate_method(CLIENT, 201, connect=db_factory)
    assert not list_methods(CLIENT, connect=db_factory)[0].active


def test_deactivation_rolls_back_written_change_on_failure(
    seeded_database, db_factory, monkeypatch
):
    conn = db_factory()
    rollback = conn.rollback
    rolled_back = False

    def fail_before_commit():
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT active FROM payment_methods WHERE payment_method_id = 201"
            )
            assert cursor.fetchone() == (0,)
        raise OperationalError("Injected pre-commit failure")

    def record_rollback():
        nonlocal rolled_back
        rollback()
        rolled_back = True

    monkeypatch.setattr(conn, "commit", fail_before_commit)
    monkeypatch.setattr(conn, "rollback", record_rollback)
    with pytest.raises(DatabaseError, match="Payment database operation failed"):
        payments.deactivate_method(CLIENT, 201, connect=lambda: conn)
    assert rolled_back
    assert not conn.is_connected()
    assert list_methods(CLIENT, connect=db_factory)[0].active
    payments.deactivate_method(CLIENT, 201, connect=db_factory)


def test_cli_deactivation_recovers_and_relists(
    seeded_database, db_factory, monkeypatch, capsys
):
    monkeypatch.setattr(
        client, "list_methods", partial(list_methods, connect=db_factory)
    )
    monkeypatch.setattr(
        client,
        "deactivate_method",
        lambda *args: payments.deactivate_method(*args, connect=db_factory),
        raising=False,
    )
    answers = iter(["1", "3", "bad", "3", "203", "3", "201", "1", "0", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    client.run(CLIENT)
    output = capsys.readouterr().out
    assert "Enter a positive method ID" in output
    assert "Invalid payment method" in output
    assert "inactive" in output
    assert "201: credit ****0201 (inactive)" in output


def test_cli_lists_and_adds_owned_methods_after_invalid_input(
    seeded_database, db_factory, monkeypatch, capsys
):
    monkeypatch.setattr(
        client,
        "list_methods",
        partial(payments.list_methods, connect=db_factory),
        raising=False,
    )
    monkeypatch.setattr(
        client,
        "add_method",
        partial(payments.add_method, connect=db_factory),
        raising=False,
    )
    number = "0000-0000-01234"
    answers = iter(
        [
            "1",
            "?",
            "1",
            "2",
            "debit",
            "123",
            "Demo Lane",
            "2",
            "credit",
            number,
            "Demo Lane",
            "1",
            "0",
            "0",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    client.run(CLIENT)

    output = capsys.readouterr().out
    assert "Invalid choice" in output
    assert "13–19 ASCII digits" in output
    assert "****0201" in output and "****0202" in output
    assert "inactive" in output and "****1234" in output and "Added" in output
    assert "0203" not in output
    assert number not in output and number.replace("-", "") not in output
