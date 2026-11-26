from decimal import Decimal
from functools import partial

import pytest
from mysql.connector import Error

from src import admin, analytics
from src.auth import Principal
from src.database import AuthorizationError, DatabaseError

ADMIN = Principal(1, "admin")


def test_theater_revenue_counts_committed_purchases_once(seeded_database, db_factory):
    def report():
        rows = analytics.revenue_by_theater(ADMIN, connect=db_factory)
        assert all(isinstance(row.revenue, Decimal) for row in rows)
        return [(row.theater_id, row.tickets_sold, row.revenue) for row in rows]

    with seeded_database.cursor() as cursor:
        cursor.execute(
            "INSERT INTO theaters (theater_id, capacity, supports_3d, enhanced_sound) "
            "VALUES (4, 10, 0, 0), (5, 10, 0, 0)"
        )
        cursor.execute("UPDATE theaters SET supports_3d = 1")
    seeded_database.commit()

    expected = [
        (3, 34, Decimal("601.20")),
        (1, 11, Decimal("159.00")),
        (2, 4, Decimal("80.00")),
        (4, 0, Decimal("0.00")),
        (5, 0, Decimal("0.00")),
    ]
    assert report() == expected

    with seeded_database.cursor() as cursor:
        cursor.execute(
            "INSERT INTO purchases (client_id, screening_id, payment_method_id, "
            "quantity, unit_price, total_amount, purchased_at) "
            "VALUES (11, 102, 201, 2, 13.25, 26.50, '2026-11-23 08:00:00')"
        )
        cursor.execute(
            "UPDATE screenings SET sold_tickets = 6 WHERE screening_id = 102"
        )
    seeded_database.commit()
    expected[2] = (2, 6, Decimal("106.50"))
    assert report() == expected


@pytest.mark.parametrize(
    "principal", [None, Principal(11, "client"), Principal(11, "admin")]
)
def test_theater_revenue_requires_verified_admin(
    seeded_database, db_factory, principal
):
    with pytest.raises(AuthorizationError):
        analytics.revenue_by_theater(principal, connect=db_factory)


def test_theater_revenue_translates_connector_errors():
    def connect():
        raise Error("Internal driver detail")

    with pytest.raises(DatabaseError, match="^Theater revenue is unavailable\\.$"):
        analytics.revenue_by_theater(ADMIN, connect=connect)


def test_cli_theater_revenue(seeded_database, db_factory, monkeypatch, capsys):
    monkeypatch.setattr(
        admin,
        "revenue_by_theater",
        partial(analytics.revenue_by_theater, connect=db_factory),
    )
    choices = iter(["5", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(choices))
    admin.run(ADMIN)
    assert capsys.readouterr().out.splitlines() == [
        "Administrator menu",
        "Revenue by theater",
        "Theater 3 | 34 tickets | EUR 601.20",
        "Theater 1 | 11 tickets | EUR 159.00",
        "Theater 2 | 4 tickets | EUR 80.00",
    ]
