"""Administrator-only reports over captured purchase data."""

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

from mysql.connector import Error
from mysql.connector.abstracts import MySQLConnectionAbstract

from src import database
from src.auth import Principal, require_role
from src.database import DatabaseError, ValidationError

_MOVIE_REVENUE = """
SELECT m.movie_id, m.title, COALESCE(SUM(p.quantity), 0) AS tickets_sold,
       COALESCE(SUM(p.total_amount), 0.00) AS revenue
FROM movies m
LEFT JOIN screenings s ON s.movie_id = m.movie_id
LEFT JOIN purchases p ON p.screening_id = s.screening_id
GROUP BY m.movie_id, m.title
HAVING COALESCE(SUM(p.quantity), 0) >= %(minimum_tickets)s
ORDER BY revenue DESC, m.movie_id ASC
"""

_THEATER_REVENUE = """
SELECT t.theater_id, COALESCE(SUM(p.quantity), 0) AS tickets_sold,
       COALESCE(SUM(p.total_amount), 0.00) AS revenue
FROM theaters t
LEFT JOIN screenings s ON s.theater_id = t.theater_id
LEFT JOIN purchases p ON p.screening_id = s.screening_id
GROUP BY t.theater_id
ORDER BY revenue DESC, t.theater_id ASC
"""


@dataclass(frozen=True)
class MovieRevenue:
    movie_id: int
    title: str
    tickets_sold: int
    revenue: Decimal


def revenue_by_movie(
    principal: Principal,
    *,
    minimum_tickets: int = 0,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> list[MovieRevenue]:
    """Summarize captured revenue for each movie meeting the ticket threshold."""
    require_role(principal, "admin")
    if type(minimum_tickets) is not int or minimum_tickets < 0:
        raise ValidationError("Enter a nonnegative whole number.")
    try:
        conn = connect()
        try:
            database.verify_principal(conn, principal, "admin")
            with conn.cursor() as cursor:
                cursor.execute(_MOVIE_REVENUE, {"minimum_tickets": minimum_tickets})
                return [
                    MovieRevenue(movie_id, title, int(tickets), revenue)
                    for movie_id, title, tickets, revenue in cursor.fetchall()
                ]
        finally:
            try:
                conn.rollback()
            finally:
                conn.close()
    except Error as exc:
        raise DatabaseError("Movie revenue is unavailable.") from exc


@dataclass(frozen=True)
class TheaterRevenue:
    theater_id: int
    tickets_sold: int
    revenue: Decimal


def revenue_by_theater(
    principal: Principal,
    *,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> list[TheaterRevenue]:
    """Summarize captured revenue and ticket quantities for every theater."""
    require_role(principal, "admin")
    try:
        conn = connect()
        try:
            database.verify_principal(conn, principal, "admin")
            with conn.cursor() as cursor:
                cursor.execute(_THEATER_REVENUE)
                return [
                    TheaterRevenue(theater_id, int(tickets), revenue)
                    for theater_id, tickets, revenue in cursor.fetchall()
                ]
        finally:
            try:
                conn.rollback()
            finally:
                conn.close()
    except Error as exc:
        raise DatabaseError("Theater revenue is unavailable.") from exc
