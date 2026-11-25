from decimal import Decimal
from functools import partial

import pytest

from src import admin, analytics
from src.auth import Principal
from src.database import AuthorizationError, ValidationError

ADMIN = Principal(1, "admin")
EXPECTED = [
    (2, 30, Decimal("540.00")),
    (1, 13, Decimal("215.00")),
    (4, 3, Decimal("43.20")),
    (3, 2, Decimal("24.00")),
    (5, 1, Decimal("18.00")),
    (6, 0, Decimal("0.00")),
    (7, 0, Decimal("0.00")),
    (8, 0, Decimal("0.00")),
]


def test_movie_revenue_uses_captured_totals(seeded_database, db_factory):
    with seeded_database.cursor() as cursor:
        cursor.execute("UPDATE theaters SET supports_3d = 1")
    seeded_database.commit()

    report = partial(analytics.revenue_by_movie, ADMIN, connect=db_factory)
    for options, expected in (({}, EXPECTED), ({"minimum_tickets": 3}, EXPECTED[:3])):
        rows = report(**options)
        assert [(r.movie_id, r.tickets_sold, r.revenue) for r in rows] == expected
        assert all(
            type(r.tickets_sold) is int and isinstance(r.revenue, Decimal) for r in rows
        )
        assert [r.title for r in rows] == [f"Fixture Movie {i}" for i, _, _ in expected]


@pytest.mark.parametrize("threshold", [-1, True, 1.5, "3", None])
def test_rejects_invalid_threshold(seeded_database, db_factory, threshold):
    with pytest.raises(ValidationError):
        analytics.revenue_by_movie(ADMIN, minimum_tickets=threshold, connect=db_factory)


@pytest.mark.parametrize(
    "principal", [None, Principal(11, "client"), Principal(11, "admin")]
)
def test_requires_verified_admin(seeded_database, db_factory, principal):
    with pytest.raises(AuthorizationError):
        analytics.revenue_by_movie(principal, connect=db_factory)


def test_cli_movie_revenue(seeded_database, db_factory, monkeypatch, capsys):
    monkeypatch.setattr(
        admin,
        "revenue_by_movie",
        partial(analytics.revenue_by_movie, connect=db_factory),
    )
    choices = iter(["4", "", "4", "-1", "4", "31", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(choices))
    admin.run(ADMIN)
    output = capsys.readouterr().out
    assert "Fixture Movie 2 | 30 tickets | EUR 540.00" in output
    assert "Fixture Movie 8 | 0 tickets | EUR 0.00" in output
    assert "Enter a nonnegative whole number." in output
    assert "No movies meet the ticket threshold." in output
