"""Authenticate preloaded accounts and check in-process principal shape."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import scrypt
from hmac import compare_digest
from typing import Literal, cast

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract

from src import database
from src.database import AuthenticationError, AuthorizationError, DatabaseError

Role = Literal["client", "admin"]
_HASH = re.compile(r"scrypt\$16384\$8\$1\$([0-9a-fA-F]{32})\$([0-9a-fA-F]{64})")


@dataclass(frozen=True)
class Principal:
    user_id: int
    role: Role


def require_role(principal: Principal, role: Role) -> None:
    """Check shape and role only; use database.verify_principal at service entry."""
    if (
        not isinstance(principal, Principal)
        or type(principal.user_id) is not int
        or principal.user_id <= 0
        or role not in ("client", "admin")
        or principal.role != role
    ):
        raise AuthorizationError("Access denied")


def authenticate(
    email: str,
    password: str,
    *,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> Principal:
    """Look up a normalized email and verify its bounded scrypt credential."""
    invalid = "Invalid email or password"
    if not isinstance(email, str) or not isinstance(password, str):
        raise AuthenticationError(invalid)
    email = email.strip().casefold()
    try:
        email.encode()
        secret = password.encode()
    except UnicodeEncodeError:
        raise AuthenticationError(invalid) from None
    if not email or len(email) > 254 or not secret:
        raise AuthenticationError(invalid)

    try:
        conn = connect()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT u.user_id, u.role, u.password_hash, cp.user_id "
                    "FROM users u LEFT JOIN client_profiles cp ON cp.user_id = u.user_id "
                    "WHERE u.email = %s",
                    (email,),
                )
                row = cursor.fetchone()
        finally:
            try:
                conn.rollback()
            finally:
                conn.close()
    except mysql.connector.Error as exc:
        raise DatabaseError("Authentication database operation failed") from exc

    match = _HASH.fullmatch(row[2]) if row else None
    # Keep the same KDF cost for missing accounts and malformed hashes.
    salt = bytes.fromhex(match[1]) if match else bytes(16)
    expected = bytes.fromhex(match[2]) if match else bytes(32)
    actual = scrypt(secret, salt=salt, n=16384, r=8, p=1, dklen=32)
    if not compare_digest(actual, expected) or match is None or row is None:
        raise AuthenticationError(invalid)
    user_id, role, _, profile = row
    if role not in ("client", "admin") or (role == "client" and profile is None):
        raise AuthenticationError(invalid)
    return Principal(user_id, cast(Role, role))
