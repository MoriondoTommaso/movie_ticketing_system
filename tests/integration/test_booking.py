from datetime import UTC, datetime
from decimal import Decimal
from functools import partial

import pytest

from src import booking, client
from src.auth import Principal
from src.database import (
    AuthorizationError,
    CapacityError,
    NotFoundError,
    ValidationError,
)

CLIENT = Principal(11, "client")


def clock():
    return datetime(2026, 11, 23, 8, tzinfo=UTC)


def test_purchase_persists_captured_discount_and_counter(seeded_database, db_factory):
    receipt = booking.book_tickets(CLIENT, 107, 2, 201, clock=clock, connect=db_factory)
    assert (receipt.quantity, receipt.unit_price, receipt.total_amount) == (
        2,
        Decimal("14.40"),
        Decimal("28.80"),
    )
    with db_factory().cursor() as cursor:
        cursor.execute(
            "SELECT client_id, screening_id, payment_method_id, quantity, unit_price, "
            "total_amount, purchased_at FROM purchases WHERE purchase_id=%s",
            (receipt.purchase_id,),
        )
        assert cursor.fetchone() == (
            11,
            107,
            201,
            2,
            Decimal("14.40"),
            Decimal("28.80"),
            datetime(2026, 11, 23, 9),
        )
        cursor.execute("SELECT sold_tickets FROM screenings WHERE screening_id=107")
        assert cursor.fetchone() == (5,)


@pytest.mark.parametrize(
    ("screening_id", "quantity", "method_id", "error"),
    [
        (999, 1, 201, NotFoundError),
        (101, 2, 201, CapacityError),
        (101, 1, 202, ValidationError),
        (101, 1, 203, ValidationError),
        (101, 1, 999, ValidationError),
    ],
)
def test_rejection_leaves_purchase_and_counter_unchanged(
    seeded_database, db_factory, screening_id, quantity, method_id, error
):
    with pytest.raises(error):
        booking.book_tickets(
            CLIENT, screening_id, quantity, method_id, clock=clock, connect=db_factory
        )
    with db_factory().cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM purchases")
        assert cursor.fetchone() == (8,)
        cursor.execute("SELECT sold_tickets FROM screenings WHERE screening_id=101")
        assert cursor.fetchone() == (9,)


def test_started_screening_and_wrong_stored_role_are_rejected(
    seeded_database, db_factory
):
    with pytest.raises(ValidationError, match="already started"):
        booking.book_tickets(
            CLIENT,
            101,
            1,
            201,
            connect=db_factory,
            clock=lambda: datetime(2026, 11, 24, 9, tzinfo=UTC),
        )
    with pytest.raises(AuthorizationError):
        booking.book_tickets(
            Principal(1, "client"), 101, 1, 201, connect=db_factory, clock=clock
        )


def test_cli_recovers_and_prints_receipt(
    seeded_database, db_factory, monkeypatch, capsys
):
    monkeypatch.setattr(
        client,
        "book_tickets",
        partial(booking.book_tickets, connect=db_factory, clock=clock),
        raising=False,
    )
    answers = iter(["3", "101", "2", "201", "3", "107", "2", "201", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    client.run(CLIENT)
    output = capsys.readouterr().out
    assert "Not enough seats" in output
    assert "Purchase 309" in output and "2 tickets" in output and "EUR 28.80" in output
