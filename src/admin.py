"""Administrator terminal adapter; features are added as services land."""

from datetime import datetime
from typing import Literal

from src.analytics import revenue_by_movie, revenue_by_theater
from src.auth import Principal
from src.database import (
    AuthorizationError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from src.screenings import (
    create_screening,
    list_capacity,
    list_languages,
    list_movies,
    list_schedule,
    list_theaters,
)


def _read_id(prompt: str) -> int:
    value = input(prompt).strip()
    if not value.isascii() or not value.isdecimal() or len(value) > 10:
        raise ValidationError("Enter a positive ID.")
    result = int(value)
    if not 0 < result < 2**32:
        raise ValidationError("Enter a positive ID.")
    return result


def _add_screening(principal: Principal) -> None:
    try:
        for movie in list_movies(principal):
            print(f"{movie.movie_id}: {movie.title}")
        movie_id = _read_id("Movie ID: ")
        for theater in list_theaters(principal):
            print(
                f"{theater.theater_id}: Theater {theater.theater_id} ({theater.capacity} seats)"
            )
        theater_id = _read_id("Theater ID: ")
        for language in list_languages(principal, movie_id=movie_id):
            print(f"{language.language_id}: {language.name}")
        language_id = _read_id("Language ID: ")
        starts_at = datetime.strptime(
            input("Start YYYY-MM-DD HH:MM: ").strip(), "%Y-%m-%d %H:%M"
        )
        screening_id = create_screening(
            principal, movie_id, theater_id, language_id, starts_at
        )
    except ValueError:
        print("Use YYYY-MM-DD HH:MM for the start.")
    except (ValidationError, NotFoundError) as exc:
        print(exc)
    except AuthorizationError:
        print("Access denied.")
    except DatabaseError:
        print("Screening could not be added. Try again.")
    else:
        print(f"Screening {screening_id} added.")


def _show_view(principal: Principal, view: Literal["schedule", "capacity"]) -> None:
    try:
        raw_date = input("Date YYYY-MM-DD (optional): ").strip()
        screening_date = (
            datetime.strptime(raw_date, "%Y-%m-%d").date() if raw_date else None
        )
        read = list_schedule if view == "schedule" else list_capacity
        rows = read(principal, screening_date=screening_date)
    except ValueError:
        print("Use YYYY-MM-DD for the date.")
        return
    except ValidationError as exc:
        print(exc)
        return
    except AuthorizationError:
        print("Access denied.")
        return
    except DatabaseError:
        print("Screening view is unavailable. Try again.")
        return

    print("Schedule" if view == "schedule" else "Remaining capacity")
    if not rows:
        print("No screenings found.")
    for row in rows:
        print(
            f"{row.screening_id}: {row.title} | Theater {row.theater_id} | "
            f"{row.starts_at:%Y-%m-%d %H:%M} | {row.language} | "
            f"{row.available_seats} seats (advisory)"
        )


def _show_movie_revenue(principal: Principal) -> None:
    try:
        raw = input("Minimum tickets (blank for 0): ").strip()
        if raw and (not raw.isascii() or not raw.isdecimal()):
            raise ValueError
        rows = revenue_by_movie(principal, minimum_tickets=int(raw or "0"))
    except (ValueError, ValidationError):
        print("Enter a nonnegative whole number.")
        return
    except AuthorizationError:
        print("Access denied.")
        return
    except DatabaseError:
        print("Movie revenue is unavailable. Try again.")
        return

    print("Revenue by movie")
    if not rows:
        print("No movies meet the ticket threshold.")
    for row in rows:
        print(f"{row.title} | {row.tickets_sold} tickets | EUR {row.revenue:.2f}")


def _show_theater_revenue(principal: Principal) -> None:
    try:
        rows = revenue_by_theater(principal)
    except AuthorizationError:
        print("Access denied.")
        return
    except DatabaseError:
        print("Theater revenue is unavailable. Try again.")
        return

    print("Revenue by theater")
    if not rows:
        print("No theaters found.")
    for row in rows:
        print(
            f"Theater {row.theater_id} | {row.tickets_sold} tickets | EUR {row.revenue:.2f}"
        )


def run(principal: Principal) -> None:
    """Run the administrator menu for the authenticated session."""
    print("Administrator menu")
    while True:
        choice = input(
            "1. Add screening\n2. View schedule\n3. View remaining capacity\n"
            "4. View analytics (revenue by movie)\n5. View revenue by theater\n0. Exit\nChoice: "
        ).strip()
        if choice == "0":
            return
        if choice == "1":
            _add_screening(principal)
        elif choice == "2":
            _show_view(principal, "schedule")
        elif choice == "3":
            _show_view(principal, "capacity")
        elif choice == "4":
            _show_movie_revenue(principal)
        elif choice == "5":
            _show_theater_revenue(principal)
        else:
            print("Invalid choice. Enter 1, 2, 3, 4, 5 or 0.")
