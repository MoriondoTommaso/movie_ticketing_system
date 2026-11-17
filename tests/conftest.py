"""Opt-in lifecycle. Tests require complete DB_* and TEST_DB_* configuration.

Use independent local Compose projects/ports per verifier. Pure guard tests inject
settings/fakes; MySQL tests fail (never skip) if settings or the server are missing.
Future schema/seed fixtures must explicitly request empty_database before loading
their artifacts; merely requesting a connection never resets or populates tables.
"""

from contextlib import ExitStack
from pathlib import Path

import pytest

from src import database


def validated_test_settings(environ=None):
    """Fail closed before connecting; local Compose targets must be distinct."""
    dev = database.settings_from_env(target="dev", environ=environ)
    test = database.settings_from_env(target="test", environ=environ)
    if (
        test.host not in ("localhost", "127.0.0.1", "::1")
        or test.port == dev.port
        or test.name.casefold() == dev.name.casefold()
        or test.user.casefold() in ("root", dev.user.casefold())
        or test.password == dev.password
        or not (
            test.name.casefold().startswith("test_")
            or test.name.casefold().endswith("_test")
        )
    ):
        raise database.ValidationError("Unsafe test database target")
    return test


def reset_test_database(*, environ=None, open_connection=None):
    """Drop base tables only after target, connected identity and grant checks."""
    settings = validated_test_settings(environ)
    factory = open_connection or database._connect
    conn = factory(settings)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DATABASE(), CURRENT_USER()")
            name, user = cursor.fetchone()
            if name != settings.name or user.rsplit("@", 1)[0] != settings.user:
                raise database.ValidationError("Unexpected test database identity")
            cursor.execute("SHOW GRANTS")
            grants = [row[0] for row in cursor.fetchall()]
            scope = "`" + settings.name.replace("_", r"\_") + "`.*"
            own_grant = False
            for grant in grants:
                if "WITH GRANT OPTION" in grant:
                    raise database.ValidationError("Unsafe test database grants")
                if grant.startswith("GRANT USAGE ON *.* TO "):
                    continue
                if f" ON {scope} TO " not in grant:
                    raise database.ValidationError("Unsafe test database grants")
                own_grant = True
            if not own_grant:
                raise database.ValidationError("Missing test database grants")
            cursor.execute(
                "SELECT TABLE_NAME FROM information_schema.tables "
                "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'",
                (settings.name,),
            )
            tables = cursor.fetchall()
            cursor.execute("SET FOREIGN_KEY_CHECKS=0")
            try:
                for (table,) in tables:
                    quoted = table.replace("`", "``")
                    cursor.execute(f"DROP TABLE `{settings.name}`.`{quoted}`")
            finally:
                cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    finally:
        try:
            conn.rollback()
        finally:
            conn.close()


@pytest.fixture
def reset_database():
    """Explicit callable reset; never an autouse fixture."""
    return reset_test_database


@pytest.fixture(scope="session")
def database_settings():
    """Validate the complete test target before any test connection is opened."""
    return validated_test_settings()


def _release(conn):
    try:
        if conn.is_connected():
            conn.rollback()
    finally:
        conn.close()


@pytest.fixture
def db_factory(database_settings):
    """Yield independent unseeded connections; close even caller-owned failures."""
    with ExitStack() as resources:

        def open_connection():
            conn = database._connect(database_settings)
            resources.callback(_release, conn)
            return conn

        yield open_connection


@pytest.fixture
def db_connection(db_factory):
    return db_factory()


@pytest.fixture
def empty_database(reset_database):
    """Destructive opt-in: guard and reset only the configured test database."""
    reset_database()
    try:
        yield
    finally:
        reset_database()


@pytest.fixture
def schema_database(empty_database, db_connection):
    """Opt-in schema load after guarded reset; no demo rows."""
    with db_connection.cursor() as cursor:
        cursor.execute((Path(__file__).resolve().parents[1] / "schema.sql").read_text())
        while cursor.nextset():
            pass
    return db_connection


@pytest.fixture
def seeded_database(schema_database):
    """Opt-in committed demo rows, visible to independent service connections."""
    with schema_database.cursor() as cursor:
        cursor.execute((Path(__file__).resolve().parents[1] / "data.sql").read_text())
        while cursor.nextset():
            pass
    return schema_database


@pytest.fixture
def probe_table(empty_database, db_connection):
    """Disposable InnoDB table; never touches the development service."""
    with db_connection.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE t03_probe (probe_id INT PRIMARY KEY) ENGINE=InnoDB"
        )
    return "t03_probe"
