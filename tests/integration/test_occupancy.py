from decimal import Decimal
from functools import partial

import pytest

from src import admin, analytics
from src.auth import Principal
from src.database import AuthorizationError

ADMIN = Principal(1, "admin")


def test_occupancy_weights_capacity_without_purchase_fanout(
    seeded_database, db_factory
):
    rows = analytics.occupancy_by_movie(ADMIN, connect=db_factory)
    assert [
        (r.movie_id, r.tickets_sold, r.offered_seats, r.occupancy_percent) for r in rows
    ] == [
        (1, 13, 30, Decimal("43.33")),
        (2, 30, 40, Decimal("75.00")),
        (3, 2, 30, Decimal("6.67")),
        (4, 3, 40, Decimal("7.50")),
        (5, 1, 50, Decimal("2.00")),
        (6, 0, 10, Decimal("0.00")),
        (7, 0, 20, Decimal("0.00")),
        (8, 0, 0, None),
    ]
    assert all(isinstance(r.occupancy_percent, Decimal) for r in rows[:-1])


@pytest.mark.parametrize(
    "principal", [None, Principal(11, "client"), Principal(11, "admin")]
)
def test_occupancy_requires_verified_admin(seeded_database, db_factory, principal):
    with pytest.raises(AuthorizationError):
        analytics.occupancy_by_movie(principal, connect=db_factory)


def test_cli_occupancy(seeded_database, db_factory, monkeypatch, capsys):
    monkeypatch.setattr(
        admin,
        "occupancy_by_movie",
        partial(analytics.occupancy_by_movie, connect=db_factory),
    )
    choices = iter(["6", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(choices))
    admin.run(ADMIN)
    output = capsys.readouterr().out
    assert "Fixture Movie 1 | 13/30 seats | 43.33%" in output
    assert "Fixture Movie 6 | 0/10 seats | 0.00%" in output
    assert "Fixture Movie 8 | 0/0 seats | N/A" in output
