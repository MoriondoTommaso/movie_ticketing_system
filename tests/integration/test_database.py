"""Configuration/guard tests are offline; connection tests require real MySQL."""

from unittest.mock import MagicMock

import mysql.connector
import pytest

from src import database

ENV = {
    "DB_HOST": "127.0.0.1",
    "DB_PORT": "3306",
    "DB_NAME": "cinema_dev",
    "DB_USER": "cinema_dev",
    "DB_PASSWORD": "fictional_dev",
    "TEST_DB_HOST": "127.0.0.1",
    "TEST_DB_PORT": "3307",
    "TEST_DB_NAME": "cinema_test",
    "TEST_DB_USER": "cinema_test",
    "TEST_DB_PASSWORD": "fictional_test",
}


def test_settings_keep_development_and_test_separate():
    dev = database.settings_from_env(target="dev", environ=ENV)
    test = database.settings_from_env(target="test", environ=ENV)
    assert (dev.name, dev.port, dev.user) == ("cinema_dev", 3306, "cinema_dev")
    assert (test.name, test.port, test.user) == ("cinema_test", 3307, "cinema_test")
    assert "fictional_test" not in repr(test)


@pytest.mark.parametrize("field", ["HOST", "PORT", "NAME", "USER", "PASSWORD"])
def test_test_settings_never_fall_back_to_development(field):
    settings = dict(ENV)
    del settings[f"TEST_DB_{field}"]
    with pytest.raises(database.ValidationError):
        database.settings_from_env(target="test", environ=settings)


@pytest.mark.parametrize("port", ["", "0", "-1", "65536", "not-a-port"])
def test_settings_reject_invalid_ports(port):
    with pytest.raises(database.ValidationError):
        database.settings_from_env(target="test", environ=ENV | {"TEST_DB_PORT": port})


def test_settings_reject_unknown_target():
    with pytest.raises(database.ValidationError):
        database.settings_from_env(target="production", environ=ENV)


@pytest.mark.parametrize(
    "overrides",
    [
        {"TEST_DB_NAME": "cinema_dev"},
        {"TEST_DB_NAME": "CINEMA_DEV"},
        {"TEST_DB_USER": "cinema_dev"},
        {"TEST_DB_PASSWORD": "fictional_dev"},
        {"TEST_DB_PORT": "3306"},
        {"TEST_DB_HOST": "remote.example"},
        {"TEST_DB_USER": "root"},
        {"TEST_DB_NAME": "mysql"},
        {"TEST_DB_NAME": "cinema"},
        {"TEST_DB_NAME": "cinema_test`; DROP DATABASE cinema_dev"},
        {"TEST_DB_PORT": "invalid"},
        {"DB_PASSWORD": ""},
        {"TEST_DB_PASSWORD": ""},
    ],
)
def test_reset_refuses_unsafe_targets_before_connecting(reset_database, overrides):
    calls = []
    with pytest.raises(database.ValidationError):
        reset_database(environ=ENV | overrides, open_connection=calls.append)
    assert calls == [], "Rejected target must issue no connection or SQL statement"


def test_reset_requires_complete_development_identity(reset_database):
    calls = []
    test_only = {key: value for key, value in ENV.items() if key.startswith("TEST_")}
    with pytest.raises(database.ValidationError):
        reset_database(environ=test_only, open_connection=calls.append)
    assert calls == []


@pytest.mark.parametrize(
    ("identity", "grants"),
    [
        (("cinema_dev", "cinema_test@%"), []),
        (("cinema_test", "root@localhost"), []),
        (("cinema_test", "cinema_test@%"), ["GRANT ALL PRIVILEGES ON *.* TO x"]),
        (
            ("cinema_test", "cinema_test@%"),
            ["GRANT ALL PRIVILEGES ON `cinema_test`.* TO x"],
        ),
        (("cinema_test", "cinema_test@%"), ["GRANT `admin_role` TO x"]),
    ],
)
def test_reset_rejects_wrong_identity_or_broad_grants_without_writes(
    reset_database, identity, grants
):
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = identity
    cursor.fetchall.return_value = [(grant,) for grant in grants]
    with pytest.raises(database.ValidationError):
        reset_database(environ=ENV, open_connection=lambda settings: conn)
    statements = [call.args[0] for call in cursor.execute.call_args_list]
    assert all(sql.startswith(("SELECT", "SHOW")) for sql in statements)
    conn.close.assert_called_once()


def test_reset_drops_only_validated_test_tables_and_restores_checks(reset_database):
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = ("cinema_test", "cinema_test@%")
    cursor.fetchall.side_effect = [
        [
            ("GRANT USAGE ON *.* TO x",),
            (r"GRANT ALL PRIVILEGES ON `cinema\_test`.* TO x",),
        ],
        [("probe`name",)],
    ]
    reset_database(environ=ENV, open_connection=lambda settings: conn)
    statements = [call.args[0] for call in cursor.execute.call_args_list]
    assert "DROP TABLE `cinema_test`.`probe``name`" in statements
    assert statements[-1] == "SET FOREIGN_KEY_CHECKS=1"
    conn.close.assert_called_once()


def test_connect_uses_settings_without_committing(monkeypatch):
    settings = database.settings_from_env(target="test", environ=ENV)
    driver = MagicMock()
    monkeypatch.setattr(database, "settings_from_env", lambda **kwargs: settings)
    monkeypatch.setattr(mysql.connector, "connect", driver)
    conn = database.connect(target="test")
    assert conn is driver.return_value
    assert driver.call_args.kwargs == {
        "host": "127.0.0.1",
        "port": 3307,
        "database": "cinema_test",
        "user": "cinema_test",
        "password": "fictional_test",
        "autocommit": False,
        "charset": "utf8mb4",
        "connection_timeout": 5,
    }
    conn.commit.assert_not_called()
    conn.close.assert_not_called()


def test_connect_closes_after_initialization_failure(monkeypatch):
    driver = MagicMock()
    driver.return_value.cursor.side_effect = mysql.connector.Error("init failed")
    monkeypatch.setattr(
        database,
        "settings_from_env",
        lambda **kwargs: database.DatabaseSettings("127.0.0.1", 3307, "x", "y", "z"),
    )
    monkeypatch.setattr(mysql.connector, "connect", driver)
    with pytest.raises(database.DatabaseError, match="Database connection failed"):
        database.connect(target="test")
    driver.return_value.close.assert_called_once()


def test_connection_context_rolls_back_and_closes_on_error(monkeypatch):
    conn = MagicMock()
    monkeypatch.setattr(database, "connect", lambda **kwargs: conn)
    with pytest.raises(RuntimeError, match="caller failed"):
        with database.connection(target="test"):
            raise RuntimeError("caller failed")
    conn.rollback.assert_called_once()
    conn.close.assert_called_once()
    conn.commit.assert_not_called()


def test_connection_closes_even_when_rollback_fails(monkeypatch):
    conn = MagicMock()
    conn.rollback.side_effect = mysql.connector.Error("rollback failed")
    monkeypatch.setattr(database, "connect", lambda **kwargs: conn)
    with pytest.raises(mysql.connector.Error, match="rollback failed"):
        with database.connection(target="test"):
            pass
    conn.close.assert_called_once()


def test_reset_restores_checks_and_closes_after_drop_failure(reset_database):
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = ("cinema_test", "cinema_test@%")
    cursor.fetchall.side_effect = [
        [(r"GRANT ALL PRIVILEGES ON `cinema\_test`.* TO x",)],
        [("probe",)],
    ]

    def execute(sql, *args):
        if sql.startswith("DROP TABLE"):
            raise mysql.connector.Error("injected drop failure")

    cursor.execute.side_effect = execute
    with pytest.raises(mysql.connector.Error, match="injected drop failure"):
        reset_database(environ=ENV, open_connection=lambda settings: conn)
    assert cursor.execute.call_args.args == ("SET FOREIGN_KEY_CHECKS=1",)
    conn.rollback.assert_called_once()
    conn.close.assert_called_once()


def test_process_environment_overrides_dotenv(monkeypatch):
    for key in ENV:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(database, "dotenv_values", lambda path: ENV)
    monkeypatch.setenv("TEST_DB_PORT", "23317")
    settings = database.settings_from_env(target="test")
    assert settings.port == 23317
    assert settings.name == "cinema_test"


def test_mysql_connections_are_independent_and_repeatable_read(db_factory):
    first, second = db_factory(), db_factory()
    ids = []
    for conn in (first, second):
        assert not conn.autocommit
        assert not conn.in_transaction
        with conn.cursor() as cursor:
            cursor.execute("SELECT CONNECTION_ID(), @@transaction_isolation")
            connection_id, isolation = cursor.fetchone()
            ids.append(connection_id)
            assert isolation == "REPEATABLE-READ"
    assert ids[0] != ids[1]


def test_mysql_probe_transactions_do_not_commit_each_other(probe_table, db_factory):
    writer, reader = db_factory(), db_factory()
    with writer.cursor() as cursor:
        cursor.execute("INSERT INTO t03_probe VALUES (1)")
    with reader.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM t03_probe")
        assert cursor.fetchone() == (0,)
    writer.rollback()
    reader.rollback()
    with reader.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM t03_probe")
        assert cursor.fetchone() == (0,)
    with writer.cursor() as cursor:
        cursor.execute("INSERT INTO t03_probe VALUES (2)")
    writer.commit()
    reader.rollback()
    with reader.cursor() as cursor:
        cursor.execute("SELECT probe_id FROM t03_probe")
        assert cursor.fetchall() == [(2,)]


def test_mysql_context_closes_and_discards_uncommitted_work(probe_table, db_factory):
    with database.connection(target="test") as success:
        with success.cursor() as cursor:
            cursor.execute("INSERT INTO t03_probe VALUES (1)")
    assert not success.is_connected()
    with pytest.raises(RuntimeError, match="injected"):
        with database.connection(target="test") as failed:
            with failed.cursor() as cursor:
                cursor.execute("INSERT INTO t03_probe VALUES (2)")
            raise RuntimeError("injected")
    assert not failed.is_connected()
    observer = db_factory()
    with observer.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM t03_probe")
        assert cursor.fetchone() == (0,)
        cursor.execute("INSERT INTO t03_probe VALUES (1)")
    observer.commit()


def test_mysql_reset_is_explicit_and_test_scoped(
    empty_database, db_factory, reset_database
):
    conn = db_factory()
    with conn.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE t03_probe (probe_id INT PRIMARY KEY) ENGINE=InnoDB"
        )
    reset_database()
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        assert cursor.fetchall() == []


def test_mysql_test_account_cannot_access_development(db_connection, database_settings):
    dev = database.settings_from_env(target="dev")
    with db_connection.cursor() as cursor:
        with pytest.raises(mysql.connector.Error) as error:
            cursor.execute(f"USE `{dev.name}`")
        assert error.value.errno == 1044
        cursor.execute("SELECT DATABASE()")
        assert cursor.fetchone() == (database_settings.name,)
