"""Authentication and principal checks against task-local MySQL accounts."""

from hashlib import scrypt
from unittest.mock import MagicMock

import pytest
from mysql.connector import IntegrityError, OperationalError

from src.auth import Principal, authenticate, require_role
from src.database import (
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    verify_principal,
)

PASSWORD = "T07 synthetic password"


@pytest.fixture
def accounts(schema_database):
    salt = b"\x07" * 16
    key = scrypt(PASSWORD.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
    encoded = f"scrypt$16384$8$1${salt.hex()}${key.hex()}"
    with schema_database.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO users (user_id,email,password_hash,role) VALUES (%s,%s,%s,%s)",
            [
                (1, "client@example.test", encoded, "client"),
                (2, "admin@example.test", encoded, "admin"),
                (3, "unprofiled@example.test", encoded, "client"),
                (4, "broken@example.test", "scrypt$invalid", "client"),
            ],
        )
        cursor.execute(
            "INSERT INTO client_profiles VALUES (1,'Task Client','Fictional Lane')"
        )
    schema_database.commit()
    return schema_database


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        (" CLIENT@EXAMPLE.TEST\t", (1, "client")),
        ("Admin@Example.Test", (2, "admin")),
    ],
)
def test_login_returns_stored_identity(accounts, db_factory, email, expected):
    principal = authenticate(email, PASSWORD, connect=db_factory)
    assert isinstance(principal, Principal)
    assert (principal.user_id, principal.role) == expected


def test_normalized_email_keys_are_unique(accounts):
    with accounts.cursor() as cursor, pytest.raises(IntegrityError) as failure:
        cursor.execute(
            "INSERT INTO users (email,password_hash,role) VALUES (%s,%s,%s)",
            (" CLIENT@EXAMPLE.TEST ".strip().casefold(), "unused", "client"),
        )
    assert failure.value.errno == 1062


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("client@example.test", "wrong"),
        ("unknown@example.test", PASSWORD),
        ("o'neil@example.test", PASSWORD),
        ("broken@example.test", PASSWORD),
        ("unprofiled@example.test", PASSWORD),
        ("", PASSWORD),
    ],
)
def test_invalid_credentials_are_indistinguishable(
    accounts, db_factory, email, password
):
    with pytest.raises(AuthenticationError, match="^Invalid email or password$"):
        authenticate(email, password, connect=db_factory)


def test_roles_are_checked_against_the_database(accounts, db_factory):
    client = authenticate("client@example.test", PASSWORD, connect=db_factory)
    admin = authenticate("admin@example.test", PASSWORD, connect=db_factory)
    require_role(client, "client")
    verify_principal(accounts, admin, "admin")
    for principal, role in [
        (None, "client"),
        ({"user_id": 1, "role": "client"}, "client"),
        (Principal(True, "client"), "client"),
        (Principal(2**100, "client"), "client"),
        (client, "admin"),
        (admin, "client"),
        (Principal(1, "admin"), "admin"),
        (Principal(3, "client"), "client"),
        (Principal(999, "client"), "client"),
    ]:
        with pytest.raises(AuthorizationError):
            verify_principal(accounts, principal, role)


def test_verifier_leaves_uncommitted_changes_with_caller(accounts, db_factory):
    with accounts.cursor() as cursor:
        cursor.execute("UPDATE users SET role='admin' WHERE user_id=1")
    verify_principal(accounts, Principal(1, "admin"), "admin")
    with db_factory().cursor() as cursor:
        cursor.execute("SELECT role FROM users WHERE user_id=1")
        assert cursor.fetchone() == ("client",)
    with accounts.cursor() as cursor:
        cursor.execute("SELECT role FROM users WHERE user_id=1")
        assert cursor.fetchone() == ("admin",)
    accounts.rollback()


@pytest.mark.parametrize("password", [PASSWORD, "wrong"])
def test_login_closes_its_connection(accounts, db_factory, password):
    conn = db_factory()
    if password == PASSWORD:
        authenticate("client@example.test", password, connect=lambda: conn)
    else:
        with pytest.raises(AuthenticationError):
            authenticate("client@example.test", password, connect=lambda: conn)
    assert not conn.is_connected()


def test_connection_failure_becomes_safe_database_error():
    def unavailable():
        raise OperationalError("private connection details")

    with pytest.raises(
        DatabaseError, match="^Authentication database operation failed$"
    ):
        authenticate("client@example.test", PASSWORD, connect=unavailable)


@pytest.mark.parametrize("rollback_fails", [False, True])
def test_query_failure_releases_owned_resources(rollback_fails):
    conn = MagicMock()
    cursor_context = conn.cursor.return_value
    cursor_context.__enter__.return_value.execute.side_effect = OperationalError(
        "private query details"
    )
    if rollback_fails:
        conn.rollback.side_effect = OperationalError("private rollback details")
    with pytest.raises(
        DatabaseError, match="^Authentication database operation failed$"
    ):
        authenticate("client@example.test", PASSWORD, connect=lambda: conn)
    cursor_context.__exit__.assert_called_once()
    conn.rollback.assert_called_once()
    conn.close.assert_called_once()
