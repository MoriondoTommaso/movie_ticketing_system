"""Administrator terminal adapter; features are added as services land."""

from src.auth import Principal


def run(principal: Principal) -> None:
    """Run the administrator menu for the authenticated session."""
    print("Administrator menu")
    while input("0. Exit\nChoice: ").strip() != "0":
        print("Invalid choice. Enter 0 to exit.")
