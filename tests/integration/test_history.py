from datetime import UTC, datetime
from decimal import Decimal
from functools import partial
from pathlib import Path

import pytest

from src import booking, client
from src.auth import Principal
from src.database import AuthorizationError
from src.payments import deactivate_method

CLIENT = Principal(11, "client")


def test_history_keeps_captured_prices_and_masked_inactive_method(
    seeded_database, db_factory
):
    receipt = booking.book_tickets(
        CLIENT,
        107,
        2,
        201,
        connect=db_factory,
        clock=lambda: datetime(2026, 11, 23, 8, tzinfo=UTC),
    )
    deactivate_method(CLIENT, 201, connect=db_factory)
    with seeded_database.cursor() as cursor:
        cursor.execute("UPDATE theaters SET supports_3d=1 WHERE theater_id=3")
    seeded_database.commit()
    rows = booking.list_purchases(CLIENT, connect=db_factory)
    assert [row.purchase_id for row in rows] == [receipt.purchase_id, 308, 303, 301]
    row = rows[0]
    assert (row.quantity, row.unit_price, row.total_amount) == (
        2,
        Decimal("14.40"),
        Decimal("28.80"),
    )
    assert (row.screening_id, row.title, row.theater_id, row.language) == (
        107,
        "Fixture Movie 4",
        3,
        "English",
    )
    assert row.masked_number == "****0201"
    assert rows[-1].masked_number == "****0202"


def test_q2_returns_only_verified_client_rows(seeded_database, db_factory):
    path = Path(__file__).resolve().parents[2] / "queries.sql"
    q2 = path.read_text().split("-- Q2:", 1)[1].split("\n", 1)[1].split(";", 1)[0]
    with seeded_database.cursor() as cursor:
        cursor.execute(q2, {"client_id": CLIENT.user_id})
        rows = cursor.fetchall()
    assert [row[0] for row in rows] == [308, 303, 301]
    assert rows == [
        tuple(vars(row).values())
        for row in booking.list_purchases(CLIENT, connect=db_factory)
    ]


@pytest.mark.parametrize(
    "principal",
    [
        None,
        Principal(1, "admin"),
        Principal(1, "client"),
        Principal("11 OR other", "client"),
    ],
)
def test_history_rejects_invalid_principals(seeded_database, db_factory, principal):
    with pytest.raises(AuthorizationError):
        booking.list_purchases(principal, connect=db_factory)


def test_cli_history_and_empty_state(seeded_database, db_factory, monkeypatch, capsys):
    with seeded_database.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users VALUES (17, 'empty@example.test', 'unused', 'client')"
        )
        cursor.execute(
            "INSERT INTO client_profiles VALUES (17, 'Empty Client', 'Demo Lane')"
        )
    seeded_database.commit()

    def run(principal):
        choices = iter(["4", "0"])
        monkeypatch.setattr("builtins.input", lambda _: next(choices))
        client.run(principal)
        return capsys.readouterr().out

    monkeypatch.setattr(
        client, "list_purchases", partial(booking.list_purchases, connect=db_factory)
    )
    assert "Purchase 301" in run(CLIENT)
    assert "No purchases found." in run(Principal(17, "client"))
