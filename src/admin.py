"""Administrator terminal adapter; features are added as services land."""

from datetime import datetime

from src.auth import Principal
from src.database import (
    AuthorizationError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from src.screenings import create_screening, list_languages, list_movies, list_theaters


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


def run(principal: Principal) -> None:
    """Run the administrator menu for the authenticated session."""
    print("Administrator menu")
    while True:
        choice = input("1. Add screening\n0. Exit\nChoice: ").strip()
        if choice == "0":
            return
        if choice == "1":
            _add_screening(principal)
        else:
            print("Invalid choice. Enter 1 or 0.")
