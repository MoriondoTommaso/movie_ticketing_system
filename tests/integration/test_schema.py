"""Real MySQL constraints; reset only through T03's guarded opt-in fixture."""

from pathlib import Path

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
