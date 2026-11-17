"""Execute the shipped SQL against the guarded, isolated MySQL target."""

from datetime import datetime
from decimal import Decimal
from hashlib import scrypt


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
