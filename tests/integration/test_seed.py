"""Execute the shipped SQL against the guarded, isolated MySQL target."""

from datetime import datetime, time, timedelta
from decimal import Decimal
from hashlib import scrypt

from src.pricing import calculate_unit_price


def test_seed_inventory_and_credentials(seeded_database):
    with seeded_database.cursor() as cursor:
        for table, expected in [
            ("users", 7),
            ("client_profiles", 6),
            ("payment_methods", 7),
            ("theaters", 3),
            ("languages", 2),
            ("genres", 2),
            ("movies", 8),
            ("movie_languages", 16),
            ("movie_genres", 10),
            ("screenings", 12),
            ("purchases", 8),
        ]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            assert cursor.fetchone() == (expected,), table
        cursor.execute("SELECT user_id, email, password_hash, role FROM users")
        salts = set()
        for user_id, email, encoded, role in cursor.fetchall():
            assert email == email.strip().casefold()
            assert role == ("admin" if user_id == 1 else "client")
            algorithm, n, r, p, salt, key = encoded.split("$")
            assert (algorithm, n, r, p) == ("scrypt", "16384", "8", "1")
            assert len(bytes.fromhex(salt)) == 16
            assert len(bytes.fromhex(key)) == 32
            salts.add(salt)
            password = "DemoAdmin-2026!" if user_id == 1 else "DemoClient-2026!"
            assert (
                scrypt(
                    password.encode(),
                    salt=bytes.fromhex(salt),
                    n=int(n),
                    r=int(r),
                    p=int(p),
                    dklen=32,
                ).hex()
                == key
            )
        assert len(salts) == 7


def test_seed_captured_totals(seeded_database):
    with seeded_database.cursor() as cursor:
        cursor.execute("SELECT SUM(quantity), SUM(total_amount) FROM purchases")
        assert cursor.fetchone() == (49, Decimal("840.20"))
        cursor.execute("SELECT DISTINCT purchased_at FROM purchases")
        assert cursor.fetchall() == [(datetime(2026, 11, 23, 8),)]


def test_fourth_capability_fixture_covers_all_eight_prices(
    pricing_database, db_factory
):
    with db_factory().cursor() as cursor:
        cursor.execute(
            "SELECT m.release_date, t.supports_3d, t.enhanced_sound "
            "FROM movies m CROSS JOIN theaters t WHERE m.movie_id IN (1,3) "
            "ORDER BY m.movie_id, t.theater_id"
        )
        prices = [
            calculate_unit_price(
                release, datetime(2026, 11, 24).date(), bool(d), bool(s)
            )
            for release, d, s in cursor.fetchall()
        ]
    assert prices == list(
        map(Decimal, ["15", "20", "18", "23", "12", "16", "14.40", "18.40"])
    )


def test_seed_relationships_schedule_and_counters(seeded_database, db_factory):
    # A second connection proves the artifact's COMMIT, not just session visibility.
    with db_factory().cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT s.*, m.release_date, m.runtime_minutes, t.capacity, "
            "t.supports_3d, t.enhanced_sound FROM screenings s "
            "JOIN movies m USING(movie_id) JOIN theaters t USING(theater_id) "
            "ORDER BY s.theater_id, s.starts_at"
        )
        screenings = cursor.fetchall()
        assert len(screenings) == 12
        previous = {}
        for row in screenings:
            start = row["starts_at"]
            end = start + timedelta(minutes=row["runtime_minutes"])
            assert start > datetime(2026, 11, 23, 9)
            assert start.second == 0 and start.time() >= time(10)
            assert end.date() == start.date() and end.time() <= time(23, 59)
            assert previous.get(row["theater_id"], datetime.min) <= start
            previous[row["theater_id"]] = end
            assert 0 <= row["sold_tickets"] <= row["capacity"]
            cursor.execute(
                "SELECT COALESCE(SUM(quantity),0) AS sold FROM purchases "
                "WHERE screening_id=%s",
                (row["screening_id"],),
            )
            assert cursor.fetchone()["sold"] == row["sold_tickets"]
            cursor.execute(
                "SELECT unit_price, quantity, total_amount, purchased_at "
                "FROM purchases WHERE screening_id=%s",
                (row["screening_id"],),
            )
            expected = calculate_unit_price(
                row["release_date"],
                start.date(),
                bool(row["supports_3d"]),
                bool(row["enhanced_sound"]),
            )
            for purchase in cursor.fetchall():
                assert purchase["unit_price"] == expected
                assert purchase["total_amount"] == expected * purchase["quantity"]
                assert purchase["purchased_at"] < start
        assert any(r["sold_tickets"] == r["capacity"] for r in screenings)
        assert any(r["sold_tickets"] == 0 for r in screenings)
        assert [
            (r["capacity"], r["sold_tickets"])
            for r in screenings
            if r["screening_id"] == 101
        ] == [(10, 9)]
        cursor.execute(
            "SELECT p.purchase_id FROM purchases p JOIN payment_methods pm "
            "USING(payment_method_id) WHERE p.client_id <> pm.client_id"
        )
        assert cursor.fetchall() == []


def test_movie_and_theater_report_oracles(seeded_database):
    with seeded_database.cursor() as cursor:
        # Separate aggregates keep screening capacities from multiplying by purchases.
        cursor.execute(
            "SELECT m.movie_id, COALESCE(p.tickets,0), COALESCE(p.revenue,0), "
            "COALESCE(s.seats,0) FROM movies m LEFT JOIN "
            "(SELECT s.movie_id, SUM(p.quantity) tickets, SUM(p.total_amount) revenue "
            "FROM screenings s JOIN purchases p USING(screening_id) "
            "GROUP BY s.movie_id) p USING(movie_id) LEFT JOIN "
            "(SELECT s.movie_id, SUM(t.capacity) seats FROM screenings s "
            "JOIN theaters t USING(theater_id) GROUP BY s.movie_id) s "
            "USING(movie_id) ORDER BY m.movie_id"
        )
        assert cursor.fetchall() == [
            (1, 13, Decimal("215.00"), 30),
            (2, 30, Decimal("540.00"), 40),
            (3, 2, Decimal("24.00"), 30),
            (4, 3, Decimal("43.20"), 40),
            (5, 1, Decimal("18.00"), 50),
            (6, 0, 0, 10),
            (7, 0, 0, 20),
            (8, 0, 0, 0),
        ]
        cursor.execute(
            "SELECT t.theater_id, SUM(p.quantity), SUM(p.total_amount) "
            "FROM theaters t JOIN screenings s USING(theater_id) "
            "JOIN purchases p USING(screening_id) GROUP BY t.theater_id "
            "ORDER BY t.theater_id"
        )
        assert cursor.fetchall() == [
            (1, 11, Decimal("159.00")),
            (2, 4, Decimal("80.00")),
            (3, 34, Decimal("601.20")),
        ]


def test_identity_history_and_search_oracles(seeded_database):
    with seeded_database.cursor() as cursor:
        cursor.execute(
            "SELECT u.user_id, cp.user_id FROM users u "
            "LEFT JOIN client_profiles cp USING(user_id) ORDER BY u.user_id"
        )
        assert cursor.fetchall() == [(1, None)] + [(i, i) for i in range(11, 17)]
        cursor.execute(
            "SELECT payment_method_id, client_id, active FROM payment_methods "
            "ORDER BY payment_method_id"
        )
        assert cursor.fetchall() == [
            (201, 11, 1),
            (202, 11, 0),
            (203, 12, 1),
            (204, 13, 1),
            (205, 14, 1),
            (206, 15, 1),
            (207, 16, 1),
        ]
        cursor.execute(
            "SELECT purchase_id, payment_method_id, total_amount FROM purchases "
            "WHERE client_id=11 ORDER BY purchased_at DESC, purchase_id DESC"
        )
        assert cursor.fetchall() == [
            (308, 201, Decimal("18")),
            (303, 201, Decimal("20")),
            (301, 202, Decimal("75")),
        ]
        cursor.execute(
            "SELECT screening_id FROM screenings ORDER BY starts_at, screening_id"
        )
        assert [r[0] for r in cursor.fetchall()] == [
            101,
            102,
            103,
            104,
            106,
            107,
            105,
            109,
            110,
            108,
            112,
            111,
        ]
        cursor.execute(
            "SELECT s.screening_id FROM screenings s JOIN movies m USING(movie_id) "
            "WHERE m.title LIKE %s AND s.language_id=2 AND DATE(s.starts_at)=%s "
            "AND TIME(s.starts_at) BETWEEN %s AND %s AND EXISTS "
            "(SELECT 1 FROM movie_genres mg WHERE mg.movie_id=m.movie_id "
            "AND mg.genre_id=1) ORDER BY s.starts_at, s.screening_id",
            ("%Movie 1%", "2026-11-24", "10:00:00", "10:00:00"),
        )
        assert cursor.fetchall() == [(101,), (102,)]
        cursor.execute(
            "SELECT m.movie_id FROM movies m WHERE NOT EXISTS "
            "(SELECT 1 FROM movie_languages ml WHERE ml.movie_id=m.movie_id "
            "AND ml.language_id=m.original_language_id) OR NOT EXISTS "
            "(SELECT 1 FROM movie_genres mg WHERE mg.movie_id=m.movie_id)"
        )
        assert cursor.fetchall() == []
