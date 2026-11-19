import pytest

from src.auth import Principal
from src.database import ValidationError
from src.payments import add_method


@pytest.mark.parametrize(
    ("kind", "number", "address"),
    [
        ("cash", "0" * 13, "Demo Lane"),
        ("credit", "0" * 12, "Demo Lane"),
        ("debit", "0" * 20, "Demo Lane"),
        ("debit", "０" * 13, "Demo Lane"),
        ("debit", "0" * 13 + "\t", "Demo Lane"),
        ("credit", "0" * 13, " \t "),
        ("credit", "0" * 13, "x" * 256),
        ("credit", True, "Demo Lane"),
    ],
)
def test_invalid_fields_do_not_open_connection(kind, number, address):
    def unexpected_connection():
        pytest.fail("Invalid fields must not open a database connection")

    with pytest.raises(ValidationError):
        add_method(
            Principal(11, "client"),
            kind,
            number,
            address,
            connect=unexpected_connection,
        )
