"""Client discovery and caller-owned screening row locks."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from mysql.connector import Error, errorcode
from mysql.connector.abstracts import MySQLConnectionAbstract

from src import database
from src.auth import Principal, require_role
from src.database import (
    DatabaseError,
    NotFoundError,
    RetryableDatabaseError,
    ValidationError,
)
from src.pricing import calculate_unit_price
from src.schedule_rules import validate_interval

_ROME = ZoneInfo("Europe/Rome")
_VIEW_SELECT = """
SELECT s.screening_id, m.movie_id, t.theater_id, m.title, l.name, s.starts_at,
       m.release_date, t.capacity - s.sold_tickets, t.supports_3d, t.enhanced_sound
FROM screenings s
JOIN movies m ON m.movie_id = s.movie_id
JOIN theaters t ON t.theater_id = s.theater_id
JOIN languages l ON l.language_id = s.language_id
"""
_SEARCH = (
    _VIEW_SELECT
    + """
WHERE s.starts_at > %(now_local)s
  AND (%(title_pattern)s IS NULL OR m.title LIKE %(title_pattern)s ESCAPE '!')
  AND (%(genre_id)s IS NULL OR EXISTS (
      SELECT 1 FROM movie_genres mg
      WHERE mg.movie_id = s.movie_id AND mg.genre_id = %(genre_id)s
  ))
  AND (%(language_id)s IS NULL OR s.language_id = %(language_id)s)
  AND (%(screening_date)s IS NULL OR DATE(s.starts_at) = %(screening_date)s)
  AND (%(time_from)s IS NULL OR TIME(s.starts_at) >= %(time_from)s)
  AND (%(time_to)s IS NULL OR TIME(s.starts_at) <= %(time_to)s)
ORDER BY s.starts_at, s.screening_id
"""
)
_SCHEDULE = (
    _VIEW_SELECT
    + """
WHERE (%(screening_date)s IS NULL OR DATE(s.starts_at) = %(screening_date)s)
ORDER BY s.starts_at, s.screening_id
"""
)


@dataclass(frozen=True)
class ScreeningView:
    screening_id: int
    movie_id: int
    theater_id: int
    title: str
    language: str
    starts_at: datetime
    unit_price: Decimal
    available_seats: int
    supports_3d: bool
    enhanced_sound: bool


@dataclass(frozen=True)
class LockedScreening:
    screening_id: int
    theater_id: int
    capacity: int
    sold_tickets: int
    runtime_minutes: int
    starts_at: datetime
    release_date: date
    supports_3d: bool
    enhanced_sound: bool


@dataclass(frozen=True)
class GenreOption:
    genre_id: int
    name: str


@dataclass(frozen=True)
class LanguageOption:
    language_id: int
    name: str


@dataclass(frozen=True)
class MovieOption:
    movie_id: int
    title: str


@dataclass(frozen=True)
class TheaterOption:
    theater_id: int
    capacity: int


@contextmanager
def _verified_read(
    principal: Principal, connect: Callable[[], MySQLConnectionAbstract]
) -> Iterator[MySQLConnectionAbstract]:
    require_role(
        principal, principal.role if isinstance(principal, Principal) else "client"
    )
    try:
        conn = connect()
        try:
            database.verify_principal(conn, principal, principal.role)
            yield conn
        finally:
            try:
                conn.rollback()
            finally:
                conn.close()
    except Error as exc:
        raise DatabaseError("Screening database read failed.") from exc


def list_genres(
    principal: Principal,
    *,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> list[GenreOption]:
    with _verified_read(principal, connect) as conn, conn.cursor() as cursor:
        cursor.execute("SELECT genre_id, name FROM genres ORDER BY genre_id")
        return [GenreOption(*row) for row in cursor.fetchall()]


def list_movies(
    principal: Principal,
    *,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> list[MovieOption]:
    with _verified_read(principal, connect) as conn, conn.cursor() as cursor:
        cursor.execute("SELECT movie_id, title FROM movies ORDER BY movie_id")
        return [MovieOption(*row) for row in cursor.fetchall()]


def list_theaters(
    principal: Principal,
    *,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> list[TheaterOption]:
    with _verified_read(principal, connect) as conn, conn.cursor() as cursor:
        cursor.execute("SELECT theater_id, capacity FROM theaters ORDER BY theater_id")
        return [TheaterOption(*row) for row in cursor.fetchall()]


def list_languages(
    principal: Principal,
    *,
    movie_id: int | None = None,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> list[LanguageOption]:
    if movie_id is not None:
        _validate_id(movie_id)
    with _verified_read(principal, connect) as conn, conn.cursor() as cursor:
        if movie_id is None:
            cursor.execute(
                "SELECT language_id, name FROM languages ORDER BY language_id"
            )
        else:
            cursor.execute(
                "SELECT movie_id FROM movies WHERE movie_id = %s", (movie_id,)
            )
            if cursor.fetchone() is None:
                raise NotFoundError("Movie not found.")
            cursor.execute(
                "SELECT l.language_id, l.name FROM languages l "
                "JOIN movie_languages ml ON ml.language_id = l.language_id "
                "WHERE ml.movie_id = %s ORDER BY l.language_id",
                (movie_id,),
            )
        return [LanguageOption(*row) for row in cursor.fetchall()]


def _validate_id(value: int) -> None:
    if type(value) is not int or not 0 < value < 2**32:
        raise ValidationError("Expected a positive ID.")


def create_screening(
    principal: Principal,
    movie_id: int,
    theater_id: int,
    language_id: int,
    starts_at: datetime,
    *,
    clock: Callable[[], datetime] = database.default_clock,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> int:
    """Serialize scheduling per theater and commit one non-overlapping screening."""
    require_role(principal, "admin")
    for value in (movie_id, theater_id, language_id):
        _validate_id(value)
    try:
        conn = connect()
        try:
            conn.start_transaction()
            database.verify_principal(conn, principal, "admin")
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT theater_id FROM theaters WHERE theater_id = %s FOR UPDATE",
                    (theater_id,),
                )
                if cursor.fetchone() is None:
                    raise NotFoundError("Theater not found.")
                instant = clock()
                if instant.utcoffset() is None:
                    raise ValidationError("Clock must return an aware datetime.")
                now_local = instant.astimezone(_ROME).replace(tzinfo=None)
                cursor.execute(
                    "SELECT runtime_minutes FROM movies WHERE movie_id = %s",
                    (movie_id,),
                )
                movie = cursor.fetchone()
                if movie is None:
                    raise NotFoundError("Movie not found.")
                cursor.execute(
                    "SELECT language_id FROM movie_languages "
                    "WHERE movie_id = %s AND language_id = %s",
                    (movie_id, language_id),
                )
                if cursor.fetchone() is None:
                    raise ValidationError("Language is not available for this movie.")
                try:
                    ends_at = validate_interval(starts_at, movie[0])
                except OverflowError:
                    raise ValidationError(
                        "Screenings must end on the same date."
                    ) from None
                if starts_at <= now_local:
                    raise ValidationError("Screening must start in the future.")
                cursor.execute(
                    "SELECT s.screening_id FROM screenings s "
                    "JOIN movies m ON m.movie_id = s.movie_id "
                    "WHERE s.theater_id = %s AND s.starts_at >= %s AND s.starts_at < %s "
                    "AND TIMESTAMPADD(MINUTE, m.runtime_minutes, s.starts_at) > %s "
                    "LIMIT 1 FOR UPDATE OF s",
                    (
                        theater_id,
                        starts_at.replace(hour=0, minute=0),
                        ends_at,
                        starts_at,
                    ),
                )
                if cursor.fetchone() is not None:
                    raise ValidationError("Screening overlaps an existing screening.")
                cursor.execute(
                    "INSERT INTO screenings (movie_id, theater_id, language_id, starts_at) "
                    "VALUES (%s, %s, %s, %s)",
                    (movie_id, theater_id, language_id, starts_at),
                )
                screening_id = cursor.lastrowid
            conn.commit()
            return screening_id
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Error as exc:
        if exc.errno in (errorcode.ER_LOCK_WAIT_TIMEOUT, errorcode.ER_LOCK_DEADLOCK):
            raise RetryableDatabaseError("Theater is busy. Try again.") from exc
        raise DatabaseError("Screening creation failed.") from exc


def search_screenings(
    principal: Principal,
    *,
    title: str | None = None,
    genre_id: int | None = None,
    language_id: int | None = None,
    screening_date: date | None = None,
    time_from: time | None = None,
    time_to: time | None = None,
    clock: Callable[[], datetime] = database.default_clock,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> list[ScreeningView]:
    """Return future screenings; displayed availability is advisory."""
    require_role(principal, "client")
    for value in (genre_id, language_id):
        if value is not None:
            _validate_id(value)
    if any(
        value is not None and (not isinstance(value, time) or value.tzinfo is not None)
        for value in (time_from, time_to)
    ):
        raise ValidationError("Use local screening times.")
    if time_from is not None and time_to is not None and time_from > time_to:
        raise ValidationError("Start time must not be later than end time.")
    if screening_date is not None and type(screening_date) is not date:
        raise ValidationError("Use a screening date.")
    if title is not None and not isinstance(title, str):
        raise ValidationError("Use a text title.")
    instant = clock()
    if instant.utcoffset() is None:
        raise ValidationError("Clock must return an aware datetime.")
    pattern = (
        None
        if title is None
        else "%" + title.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"
    )
    params = dict(
        title_pattern=pattern,
        genre_id=genre_id,
        language_id=language_id,
        screening_date=screening_date,
        time_from=time_from,
        time_to=time_to,
        now_local=instant.astimezone(_ROME).replace(tzinfo=None),
    )
    with _verified_read(principal, connect) as conn, conn.cursor() as cursor:
        cursor.execute(_SEARCH, params)
        rows = cursor.fetchall()
    return _screening_views(rows)


def _screening_views(rows) -> list[ScreeningView]:
    return [
        ScreeningView(
            sid,
            mid,
            tid,
            name,
            language,
            starts,
            calculate_unit_price(release, starts.date(), bool(three_d), bool(sound)),
            available,
            bool(three_d),
            bool(sound),
        )
        for sid, mid, tid, name, language, starts, release, available, three_d, sound in rows
    ]


def list_schedule(
    principal: Principal,
    *,
    screening_date: date | None = None,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> list[ScreeningView]:
    """List the admin schedule, including historical screenings."""
    require_role(principal, "admin")
    if screening_date is not None and type(screening_date) is not date:
        raise ValidationError("Use a screening date.")
    with _verified_read(principal, connect) as conn, conn.cursor() as cursor:
        cursor.execute(_SCHEDULE, {"screening_date": screening_date})
        return _screening_views(cursor.fetchall())


def list_capacity(
    principal: Principal,
    *,
    screening_date: date | None = None,
    connect: Callable[[], MySQLConnectionAbstract] = database.connect,
) -> list[ScreeningView]:
    """List advisory seat counts using the same records as the admin schedule."""
    return list_schedule(principal, screening_date=screening_date, connect=connect)


def lock_screening(conn: MySQLConnectionAbstract, screening_id: int) -> LockedScreening:
    """Read and lock the current screening on the caller's transaction."""
    _validate_id(screening_id)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT s.screening_id, t.theater_id, t.capacity, s.sold_tickets, "
                "m.runtime_minutes, s.starts_at, m.release_date, "
                "t.supports_3d, t.enhanced_sound "
                "FROM screenings s JOIN movies m ON m.movie_id = s.movie_id "
                "JOIN theaters t ON t.theater_id = s.theater_id "
                "WHERE s.screening_id = %s FOR UPDATE OF s",
                (screening_id,),
            )
            row = cursor.fetchone()
    except Error as exc:
        if exc.errno in (errorcode.ER_LOCK_WAIT_TIMEOUT, errorcode.ER_LOCK_DEADLOCK):
            raise RetryableDatabaseError("Screening is busy. Try again.") from exc
        raise DatabaseError("Screening lookup failed.") from exc
    if row is None:
        raise NotFoundError("Screening not found.")
    return LockedScreening(*row[:7], bool(row[7]), bool(row[8]))
