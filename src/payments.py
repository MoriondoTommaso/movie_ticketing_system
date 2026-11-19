"""Client-owned synthetic payment methods; no prompts or payment processing."""

import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal

from mysql.connector import Error, errorcode
from mysql.connector.abstracts import MySQLConnectionAbstract

from src import database
from src.auth import Principal, require_role
from src.database import DatabaseError, RetryableDatabaseError, ValidationError

PaymentType = Literal["credit", "debit"]
Connect = Callable[[], MySQLConnectionAbstract]
_METHOD_COLUMNS = (
    "payment_method_id, client_id, payment_type, card_number, billing_address, active"
)


@dataclass(frozen=True)
class PaymentMethod:
    payment_method_id: int
    client_id: int
    payment_type: PaymentType
    masked_number: str
    billing_address: str
    active: bool


def _view(
    method_id: int,
    owner: int,
    kind: PaymentType,
    number: str,
    address: str,
    active: bool,
) -> PaymentMethod:
    return PaymentMethod(
        method_id, owner, kind, f"****{number[-4:]}", address, bool(active)
    )


def _database_error(exc: Error) -> DatabaseError:
    if exc.errno in (errorcode.ER_LOCK_WAIT_TIMEOUT, errorcode.ER_LOCK_DEADLOCK):
        return RetryableDatabaseError("Payment method is busy. Try again.")
    return DatabaseError("Payment database operation failed.")


@contextmanager
def _owned_connection(
    connect: Connect, principal: Principal, *, write: bool = False
) -> Iterator[MySQLConnectionAbstract]:
    require_role(principal, "client")
    try:
        conn = connect()
        committed = False
        try:
            if write:
                conn.start_transaction()
            database.verify_principal(conn, principal, "client")
            yield conn
            if write:
                conn.commit()
                committed = True
        finally:
            try:
                if not committed:
                    conn.rollback()
            finally:
                conn.close()
    except Error as exc:
        raise _database_error(exc) from exc


def list_methods(
    principal: Principal, *, connect: Connect = database.connect
) -> list[PaymentMethod]:
    """List only the authenticated client's methods, including inactive ones."""
    with _owned_connection(connect, principal) as conn, conn.cursor() as cursor:
        cursor.execute(
            f"SELECT {_METHOD_COLUMNS} FROM payment_methods "
            "WHERE client_id = %s ORDER BY payment_method_id",
            (principal.user_id,),
        )
        return [_view(*row) for row in cursor.fetchall()]


def add_method(
    principal: Principal,
    payment_type: PaymentType,
    card_number: str,
    billing_address: str,
    *,
    connect: Connect = database.connect,
) -> PaymentMethod:
    """Validate and commit one synthetic method, returning only masked digits."""
    require_role(principal, "client")
    if payment_type not in ("credit", "debit"):
        raise ValidationError("Payment type must be credit or debit.")
    number = (
        card_number.replace(" ", "").replace("-", "")
        if isinstance(card_number, str)
        else ""
    )
    if not re.fullmatch(r"[0-9]{13,19}", number):
        raise ValidationError("Synthetic card number must contain 13–19 ASCII digits.")
    address = billing_address.strip() if isinstance(billing_address, str) else ""
    if not address or len(address) > 255:
        raise ValidationError("Enter a billing address of 1–255 characters.")
    try:
        address.encode()
    except UnicodeEncodeError:
        raise ValidationError("Billing address must be valid Unicode text.") from None

    with (
        _owned_connection(connect, principal, write=True) as conn,
        conn.cursor() as cursor,
    ):
        cursor.execute(
            "INSERT INTO payment_methods (client_id, payment_type, card_number, "
            "billing_address) VALUES (%s, %s, %s, %s)",
            (principal.user_id, payment_type, number, address),
        )
        return _view(
            cursor.lastrowid, principal.user_id, payment_type, number, address, True
        )


def lock_valid_method(
    conn: MySQLConnectionAbstract, principal: Principal, payment_method_id: int
) -> PaymentMethod:
    """Lock an owned active method on the caller's transaction, after screening."""
    require_role(principal, "client")
    invalid = "Invalid payment method"
    if type(payment_method_id) is not int or not 0 < payment_method_id < 2**32:
        raise ValidationError(invalid)
    database.verify_principal(conn, principal, "client")
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT {_METHOD_COLUMNS} FROM payment_methods "
                "WHERE payment_method_id = %s AND client_id = %s FOR UPDATE",
                (payment_method_id, principal.user_id),
            )
            row = cursor.fetchone()
    except Error as exc:
        raise _database_error(exc) from exc
    if row is None or not row[5]:
        raise ValidationError(invalid)
    return _view(*row)
