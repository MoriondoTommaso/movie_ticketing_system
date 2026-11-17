"""Real MySQL constraints; reset only through T03's guarded opt-in fixture."""

from decimal import Decimal
from pathlib import Path

import mysql.connector
import pytest

SCHEMA = Path(__file__).resolve().parents[2] / "schema.sql"
TABLES = {
    "users",
    "client_profiles",
    "payment_methods",
    "theaters",
    "languages",
    "genres",
    "movies",
    "movie_languages",
    "movie_genres",
    "screenings",
    "purchases",
}


@pytest.fixture
def schema_connection(empty_database, db_connection):
    with db_connection.cursor() as cursor:
        cursor.execute(SCHEMA.read_text())
        while cursor.nextset():
            pass
    return db_connection


def test_clean_schema_has_all_entities_and_transactional_storage(schema_connection):
    with schema_connection.cursor() as cursor:
        cursor.execute(
            "SELECT TABLE_NAME, ENGINE, TABLE_COLLATION "
            "FROM information_schema.tables WHERE TABLE_SCHEMA = DATABASE()"
        )
        tables = cursor.fetchall()
        assert {name for name, _, _ in tables} == TABLES
        assert all(engine == "InnoDB" for _, engine, _ in tables)
        assert all(collation.startswith("utf8mb4_") for _, _, collation in tables)
        cursor.execute(
            "SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.columns "
            "WHERE TABLE_SCHEMA = DATABASE() AND IS_NULLABLE = 'YES'"
        )
        assert cursor.fetchall() == [], "T01 requires every attribute to be mandatory"


@pytest.fixture
def populated_schema(schema_connection):
    """One valid row per entity; synthetic values, not the T06 seed artifact."""
    statements = [
        "INSERT INTO users VALUES (1, 'client@example.invalid', 'test-hash', 'client')",
        "INSERT INTO client_profiles VALUES (1, 'Test Client', 'Synthetic address')",
        "INSERT INTO payment_methods VALUES "
        "(1, 1, 'credit', '0000000000000', 'Synthetic address', 1)",
        "INSERT INTO theaters VALUES (1, 10, 0, 0)",
        "INSERT INTO languages VALUES (1, 'Italian'), (2, 'English')",
        "INSERT INTO genres VALUES (1, 'Drama')",
        "INSERT INTO movies VALUES "
        "(1, 'Test Film', '2020-01-01', 90, 1, 'Synthetic description')",
        "INSERT INTO movie_languages VALUES (1, 1)",
        "INSERT INTO movie_genres VALUES (1, 1)",
        "INSERT INTO screenings VALUES (1, 1, 1, 1, '2030-01-01 12:00:00', 1)",
        "INSERT INTO purchases VALUES (1, 1, 1, 1, 1, 15.00, 15.00, "
        "'2029-12-01 10:00:00')",
    ]
    with schema_connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
    return schema_connection


@pytest.mark.parametrize(
    ("table", "column", "value"),
    [
        ("users", "role", "owner"),
        ("users", "role", "CLIENT"),
        ("payment_methods", "payment_type", "cash"),
        ("payment_methods", "payment_type", "CREDIT"),
        ("payment_methods", "active", -1),
        ("payment_methods", "active", 2),
        ("payment_methods", "card_number", "0" * 12),
        ("payment_methods", "card_number", "0" * 12 + "x"),
        ("payment_methods", "card_number", "０" * 13),
        ("payment_methods", "card_number", "0" * 12 + "\n"),
        ("theaters", "capacity", 0),
        ("theaters", "capacity", -1),
        ("theaters", "supports_3d", 2),
        ("theaters", "enhanced_sound", -1),
        ("movies", "runtime_minutes", 0),
        ("movies", "runtime_minutes", -1),
        ("screenings", "sold_tickets", -1),
        ("purchases", "unit_price", -1),
        ("purchases", "total_amount", -1),
        ("purchases", "total_amount", 14.99),
    ],
)
def test_local_checks_reject_invalid_values(populated_schema, table, column, value):
    # Identifiers are fixed test parameters, never application input.
    with populated_schema.cursor() as cursor:
        with pytest.raises(mysql.connector.Error) as error:
            cursor.execute(f"UPDATE {table} SET {column} = %s", (value,))
        assert error.value.errno == 3819, "Must fail a CHECK, not unrelated SQL"


@pytest.mark.parametrize("quantity", [0, -1])
def test_quantity_must_be_positive_even_when_amount_equation_holds(
    populated_schema, quantity
):
    with populated_schema.cursor() as cursor:
        with pytest.raises(mysql.connector.Error) as error:
            cursor.execute(
                "UPDATE purchases SET quantity = %s, unit_price = 0, total_amount = 0",
                (quantity,),
            )
        assert error.value.errno == 3819
        assert "ck_purchase_quantity" in str(error.value)


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO users VALUES (2, 'client@example.invalid', 'hash', 'client')",
        "INSERT INTO languages VALUES (3, 'Italian')",
        "INSERT INTO genres VALUES (2, 'Drama')",
        "INSERT INTO movie_languages VALUES (1, 1)",
        "INSERT INTO movie_genres VALUES (1, 1)",
    ],
)
def test_unique_values_and_associations_reject_duplicates(populated_schema, statement):
    with populated_schema.cursor() as cursor:
        with pytest.raises(mysql.connector.IntegrityError) as error:
            cursor.execute(statement)
        assert error.value.errno == 1062


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO client_profiles VALUES (99, 'Missing user', 'Synthetic')",
        "UPDATE payment_methods SET client_id = 99",
        "UPDATE movies SET original_language_id = 99",
        "INSERT INTO movie_languages VALUES (99, 1)",
        "INSERT INTO movie_languages VALUES (1, 99)",
        "INSERT INTO movie_genres VALUES (99, 1)",
        "INSERT INTO movie_genres VALUES (1, 99)",
        "UPDATE screenings SET theater_id = 99",
        "UPDATE screenings SET movie_id = 99",
        "UPDATE screenings SET language_id = 99",
        # Language 2 exists, but is not available for this movie.
        "UPDATE screenings SET language_id = 2",
        "UPDATE purchases SET client_id = 99",
        "UPDATE purchases SET screening_id = 99",
        "UPDATE purchases SET payment_method_id = 99",
    ],
)
def test_missing_parents_and_unavailable_language_are_rejected(
    populated_schema, statement
):
    with populated_schema.cursor() as cursor:
        with pytest.raises(mysql.connector.IntegrityError) as error:
            cursor.execute(statement)
        assert error.value.errno == 1452


def test_purchase_retains_payment_but_allows_deactivation(populated_schema):
    with populated_schema.cursor() as cursor:
        with pytest.raises(mysql.connector.IntegrityError) as error:
            cursor.execute("DELETE FROM payment_methods WHERE payment_method_id = 1")
        assert error.value.errno == 1451
        cursor.execute(
            "UPDATE payment_methods SET active = 0 WHERE payment_method_id = 1"
        )
        cursor.execute(
            "SELECT p.purchase_id, m.active FROM purchases p JOIN payment_methods m "
            "ON p.payment_method_id = m.payment_method_id"
        )
        assert cursor.fetchall() == [(1, 0)]


def test_valid_boundaries_and_repeated_synthetic_cards(populated_schema):
    with populated_schema.cursor() as cursor:
        cursor.execute("UPDATE theaters SET capacity = 1, supports_3d = 1")
        cursor.execute("UPDATE movies SET runtime_minutes = 1")
        cursor.execute("UPDATE screenings SET sold_tickets = 0")
        cursor.execute(
            "UPDATE purchases SET quantity = 2, unit_price = 0, total_amount = 0"
        )
        cursor.execute(
            "INSERT INTO payment_methods (client_id, payment_type, card_number, "
            "billing_address) VALUES (1, 'debit', %s, 'Synthetic')",
            ("0" * 19,),
        )
        cursor.execute("UPDATE payment_methods SET card_number = %s", ("0" * 13,))
        cursor.execute("SELECT active, card_number FROM payment_methods ORDER BY 1")
        assert cursor.fetchall() == [(1, "0" * 13), (1, "0" * 13)]
        cursor.execute("SELECT quantity, unit_price, total_amount FROM purchases")
        assert cursor.fetchone() == (2, 0, 0)
        cursor.execute(
            "UPDATE purchases SET quantity = 3, unit_price = %s, total_amount = %s",
            (Decimal("12.34"), Decimal("37.02")),
        )
        cursor.execute("SELECT quantity, unit_price, total_amount FROM purchases")
        assert cursor.fetchone() == (3, Decimal("12.34"), Decimal("37.02"))


def test_lookup_and_history_indexes(schema_connection):
    expected = {
        ("screenings", ("theater_id", "starts_at")),
        ("screenings", ("movie_id", "starts_at")),
        ("screenings", ("starts_at", "screening_id")),
        ("purchases", ("client_id", "purchased_at", "purchase_id")),
        ("purchases", ("screening_id",)),
        ("payment_methods", ("client_id", "active")),
        ("movie_languages", ("language_id", "movie_id")),
        ("movie_genres", ("genre_id", "movie_id")),
    }
    with schema_connection.cursor() as cursor:
        cursor.execute(
            "SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME FROM information_schema.statistics "
            "WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX"
        )
        indexes = {}
        for table, index, column in cursor.fetchall():
            indexes.setdefault((table, index), []).append(column)
        actual = {(table, tuple(cols)) for (table, _), cols in indexes.items()}
        assert expected <= actual
