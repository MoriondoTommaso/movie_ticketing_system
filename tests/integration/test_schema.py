"""Real MySQL constraints; reset only through T03's guarded opt-in fixture."""

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
        ("purchases", "quantity", 0),
        ("purchases", "quantity", -1),
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
