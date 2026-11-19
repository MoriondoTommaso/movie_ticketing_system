"""Client terminal adapter; features are added as services land."""

from datetime import date, time

from src.auth import Principal
from src.database import AuthorizationError, DatabaseError, ValidationError
from src.payments import PaymentMethod, add_method, deactivate_method, list_methods
from src.screenings import list_genres, list_languages, search_screenings


def _show_method(method: PaymentMethod) -> None:
    state = "active" if method.active else "inactive"
    print(
        f"{method.payment_method_id}: {method.payment_type} {method.masked_number} ({state})"
    )


def _manage_payment_methods(principal: Principal) -> None:
    while True:
        choice = input(
            "1. List methods\n2. Add method\n3. Deactivate method\n0. Back\nChoice: "
        ).strip()
        if choice == "0":
            return
        try:
            if choice == "1":
                methods = list_methods(principal)
                if not methods:
                    print("No payment methods.")
                for method in methods:
                    _show_method(method)
            elif choice == "2":
                kind = input("Payment type (credit/debit): ").strip().lower()
                if kind not in ("credit", "debit"):
                    print("Payment type must be credit or debit.")
                    continue
                number = input("Synthetic card number (never enter a real card): ")
                address = input("Billing address: ")
                added = add_method(principal, kind, number, address)
                print("Added payment method:")
                _show_method(added)
            elif choice == "3":
                raw_id = input("Method ID to permanently deactivate: ").strip()
                if not raw_id.isascii() or not raw_id.isdecimal() or len(raw_id) > 10:
                    print("Enter a positive method ID.")
                    continue
                method_id = int(raw_id)
                if method_id == 0:
                    print("Enter a positive method ID.")
                    continue
                deactivate_method(principal, method_id)
                print("Payment method is inactive.")
            else:
                print("Invalid choice. Enter 1, 2, 3 or 0.")
        except ValidationError as exc:
            print(exc)
        except DatabaseError:
            print("Payment methods are unavailable. Try again.")
        except AuthorizationError:
            print("Access denied.")
            return


def _optional_input(prompt, parse):
    value = input(prompt).strip()
    return parse(value) if value else None


def _search(principal: Principal) -> None:
    try:
        title = _optional_input("Title substring (optional): ", str)
        print("Genres:")
        for genre in list_genres(principal):
            print(f"{genre.genre_id}: {genre.name}")
        genre_id = _optional_input("Genre ID (optional): ", int)
        print("Languages:")
        for language in list_languages(principal):
            print(f"{language.language_id}: {language.name}")
        language_id = _optional_input("Language ID (optional): ", int)
        rows = search_screenings(
            principal,
            title=title,
            genre_id=genre_id,
            language_id=language_id,
            screening_date=_optional_input(
                "Date YYYY-MM-DD (optional): ", date.fromisoformat
            ),
            time_from=_optional_input("From HH:MM (optional): ", time.fromisoformat),
            time_to=_optional_input("To HH:MM (optional): ", time.fromisoformat),
        )
    except ValueError:
        print("Use numeric IDs, YYYY-MM-DD dates, and HH:MM times.")
        return
    except ValidationError as exc:
        print(exc)
        return
    except AuthorizationError:
        print("Access denied.")
        return
    except DatabaseError:
        print("Screening search is unavailable. Try again.")
        return

    if not rows:
        print("No screenings found.")
    for row in rows:
        print(
            f"{row.screening_id}: {row.title} | Theater {row.theater_id} | "
            f"{row.starts_at:%Y-%m-%d %H:%M} | {row.language} | EUR {row.unit_price:.2f} | "
            f"{row.available_seats} seats (advisory) | "
            f"3D: {'yes' if row.supports_3d else 'no'} | "
            f"Enhanced sound: {'yes' if row.enhanced_sound else 'no'}"
        )


def run(principal: Principal) -> None:
    """Run the client menu for the authenticated session."""
    print("Client menu")
    while True:
        choice = input(
            "1. Manage payment methods\n2. Search screenings\n0. Exit\nChoice: "
        ).strip()
        if choice == "0":
            return
        if choice == "1":
            _manage_payment_methods(principal)
        elif choice == "2":
            _search(principal)
        else:
            print("Invalid choice. Enter 1, 2 or 0.")
