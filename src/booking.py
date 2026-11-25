"""Atomic purchases of tickets using synthetic payment methods."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from mysql.connector import Error, errorcode
from mysql.connector.abstracts import MySQLConnectionAbstract, MySQLCursorAbstract

from src import database
from src.auth import Principal, require_role
from src.database import (
    CapacityError,
    DatabaseError,
    RetryableDatabaseError,
    ValidationError,
)
from src.payments import lock_valid_method
from src.pricing import calculate_unit_price
from src.screenings import lock_screening

_ROME = ZoneInfo("Europe/Rome")


@contextmanager
def _write_cursor(conn: MySQLConnectionAbstract) -> Iterator[MySQLCursorAbstract]:
    cursor = conn.cursor()
    try:
        yield cursor
    except BaseException:
        with suppress(Error):
            cursor.close()
        raise
    else:
        cursor.close()


@dataclass(frozen=True)
class BookingReceipt:
    purchase_id: int
    quantity: int
    unit_price: Decimal
    total_amount: Decimal


def book_tickets(
    principal: Principal,
    screening_id: int,
    quantity: int,
    payment_method_id: int,
    *,
    clock: Callable[[], datetime] = database.default_clock,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> BookingReceipt:
    """Lock screening then payment; commit the purchase and counter together."""
    require_role(principal, "client")
    if type(quantity) is not int or quantity <= 0:
        raise ValidationError("Ticket quantity must be a positive integer.")
    try:
        conn = connect()
        try:
            conn.start_transaction()
            database.verify_principal(conn, principal, "client")
            screening = lock_screening(conn, screening_id)
            instant = clock()
            if instant.utcoffset() is None:
                raise ValidationError("Clock must return an aware datetime.")
            now_local = instant.astimezone(_ROME).replace(tzinfo=None)
            if screening.starts_at <= now_local:
                raise ValidationError("Screening has already started.")
            if quantity > screening.capacity - screening.sold_tickets:
                raise CapacityError("Not enough seats available.")
            method = lock_valid_method(conn, principal, payment_method_id)
            unit_price = calculate_unit_price(
                screening.release_date,
                screening.starts_at.date(),
                screening.supports_3d,
                screening.enhanced_sound,
            )
            total = unit_price * quantity
            with _write_cursor(conn) as cursor:
                cursor.execute(
                    "INSERT INTO purchases (client_id, screening_id, payment_method_id, "
                    "quantity, unit_price, total_amount, purchased_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (
                        principal.user_id,
                        screening.screening_id,
                        method.payment_method_id,
                        quantity,
                        unit_price,
                        total,
                        now_local,
                    ),
                )
                receipt = BookingReceipt(cursor.lastrowid, quantity, unit_price, total)
                cursor.execute(
                    "UPDATE screenings SET sold_tickets = sold_tickets + %s "
                    "WHERE screening_id = %s",
                    (quantity, screening.screening_id),
                )
            try:
                conn.commit()
            except Error as exc:
                if exc.errno in (
                    errorcode.ER_LOCK_WAIT_TIMEOUT,
                    errorcode.ER_LOCK_DEADLOCK,
                ):
                    raise
                raise DatabaseError(
                    "Booking outcome is unknown. Check before trying again."
                ) from exc
        except BaseException:
            # Cleanup must not hide the reason for failure (including a lost ACK).
            with suppress(Error):
                conn.rollback()
            with suppress(Error):
                conn.close()
            raise
        # A cleanup error cannot undo an acknowledged commit.
        with suppress(Error):
            conn.close()
        return receipt
    except Error as exc:
        if exc.errno in (errorcode.ER_LOCK_WAIT_TIMEOUT, errorcode.ER_LOCK_DEADLOCK):
            raise RetryableDatabaseError("Booking is busy. Try again.") from exc
        raise DatabaseError("Booking could not be completed.") from exc
