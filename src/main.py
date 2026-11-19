"""Canonical terminal entry point: python -m src.main."""

from getpass import GetPassWarning, getpass
from warnings import catch_warnings, simplefilter

from src import admin, client
from src.auth import authenticate
from src.database import AuthenticationError, DatabaseError, ValidationError


def main() -> None:
    """Authenticate before opening a role-specific menu."""
    try:
        while True:
            email = input("Email (0 to exit): ").strip()
            if email == "0":
                break
            if not email:
                print("Enter an email or 0 to exit.")
                continue
            with catch_warnings():
                simplefilter("error", GetPassWarning)
                password = getpass("Password: ")
            try:
                principal = authenticate(email, password)
            except AuthenticationError:
                print("Invalid email or password. Try again.")
                continue
            except DatabaseError:
                print("Database unavailable. Try again or enter 0 to exit.")
                continue
            except ValidationError:
                print("Database configuration is invalid. Check settings or exit.")
                continue
            finally:
                del password
            if principal.role == "client":
                client.run(principal)
            elif principal.role == "admin":
                admin.run(principal)
            else:
                print("Unrecognized account role.")
            break
    except (EOFError, KeyboardInterrupt):
        pass
    except GetPassWarning:
        print("Cannot read a hidden password. Run from an interactive terminal.")
    print("Goodbye.")


if __name__ == "__main__":
    main()
