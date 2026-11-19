"""Explicit MySQL settings and connections; callers own transactions/resources."""

import os
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import mysql.connector
from dotenv import dotenv_values
from mysql.connector.abstracts import MySQLConnectionAbstract

if TYPE_CHECKING:
    from src.auth import Principal, Role

Target = Literal["dev", "test"]


class CinemaError(Exception):
    """Base for service failures safe to translate at the interface boundary."""


class ValidationError(CinemaError):
    """Invalid configuration or application input."""


class AuthenticationError(CinemaError):
    """Credentials could not be verified."""


class AuthorizationError(CinemaError):
    """The principal is not allowed to perform the requested operation."""


class DatabaseError(CinemaError):
    """A database operation failed; do not expose driver details to users."""


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str = field(repr=False)


def settings_from_env(
    *, target: Target = "dev", environ: Mapping[str, str] | None = None
) -> DatabaseSettings:
    """Read one complete target; process settings override the repository .env."""
    if target not in ("dev", "test"):
        raise ValidationError("Unknown database target")
    if environ is None:
        environ = {
            **dotenv_values(Path(__file__).resolve().parents[1] / ".env"),
            **os.environ,
        }
    prefix = "DB" if target == "dev" else "TEST_DB"
    values = {}
    for key in ("HOST", "PORT", "NAME", "USER", "PASSWORD"):
        value = environ.get(f"{prefix}_{key}")
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"Missing {prefix}_{key}")
        values[key] = value
    if not values["PORT"].isascii() or not values["PORT"].isdecimal():
        raise ValidationError(f"Invalid {prefix}_PORT")
    port = int(values["PORT"])
    if not 1 <= port <= 65535:
        raise ValidationError(f"Invalid {prefix}_PORT")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", values["NAME"]):
        raise ValidationError(f"Invalid {prefix}_NAME")
    return DatabaseSettings(
        values["HOST"], port, values["NAME"], values["USER"], values["PASSWORD"]
    )


def _connect(settings: DatabaseSettings) -> MySQLConnectionAbstract:
    """Open exactly this settings snapshot; used by the guarded test lifecycle."""
    conn = None
    try:
        conn = mysql.connector.connect(
            host=settings.host,
            port=settings.port,
            database=settings.name,
            user=settings.user,
            password=settings.password,
            autocommit=False,
            charset="utf8mb4",
            connection_timeout=5,
        )
        with conn.cursor() as cursor:
            cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        return conn
    except mysql.connector.Error as exc:
        if conn is not None:
            conn.close()
        raise DatabaseError("Database connection failed") from exc


def connect(*, target: Target = "dev") -> MySQLConnectionAbstract:
    """Return a new connection; caller commits/rolls back and closes resources."""
    return _connect(settings_from_env(target=target))


def verify_principal(
    conn: MySQLConnectionAbstract, principal: "Principal", required_role: "Role"
) -> None:
    """Verify the stored role/profile without owning the caller's transaction."""
    from src.auth import require_role

    require_role(principal, required_role)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT u.role, cp.user_id FROM users u "
                "LEFT JOIN client_profiles cp ON cp.user_id = u.user_id "
                "WHERE u.user_id = %s",
                (principal.user_id,),
            )
            row = cursor.fetchone()
    except mysql.connector.Error as exc:
        raise DatabaseError("Principal verification failed") from exc
    if (
        row is None
        or row[0] != required_role
        or (required_role == "client" and row[1] is None)
    ):
        raise AuthorizationError("Access denied")


@contextmanager
def connection(*, target: Target = "dev") -> Iterator[MySQLConnectionAbstract]:
    """Optional closing scope: never commit; roll back pending work on exit."""
    conn = connect(target=target)
    try:
        yield conn
    finally:
        try:
            conn.rollback()
        finally:
            conn.close()
