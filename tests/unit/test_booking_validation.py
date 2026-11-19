from unittest.mock import Mock

import pytest

from src import booking
from src.auth import Principal
from src.database import ValidationError


@pytest.mark.parametrize("quantity", [0, -1, True, 1.5, "2"])
def test_invalid_quantity_never_connects(quantity):
    connect = Mock()
    with pytest.raises(ValidationError):
        booking.book_tickets(
            Principal(11, "client"), 101, quantity, 201, connect=connect
        )
    connect.assert_not_called()
