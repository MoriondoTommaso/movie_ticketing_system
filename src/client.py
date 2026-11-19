"""Client terminal adapter; features are added as services land."""

from src.auth import Principal


def run(principal: Principal) -> None:
    """Run the client menu for the authenticated session."""
    print("Client menu")
    while input("0. Exit\nChoice: ").strip() != "0":
        print("Invalid choice. Enter 0 to exit.")
