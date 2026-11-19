import subprocess
import sys
import warnings
from getpass import GetPassWarning
from unittest.mock import Mock

import pytest

from src import main
from src.auth import Principal
from src.database import AuthenticationError, DatabaseError, ValidationError


def script(monkeypatch, *answers):
    lines = iter(answers)

    def read(_prompt):
        try:
            return next(lines)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", read)


@pytest.mark.parametrize("role", ["client", "admin"])
def test_dispatch_uses_authenticated_principal(monkeypatch, role):
    script(monkeypatch, "admin@example.test")
    principal = Principal(12, role)
    login = Mock(return_value=principal)
    client, admin = Mock(), Mock()
    monkeypatch.setattr(main, "authenticate", login)
    monkeypatch.setattr(main, "getpass", Mock(return_value="private password"))
    monkeypatch.setattr(main.client, "run", client)
    monkeypatch.setattr(main.admin, "run", admin)

    main.main()

    login.assert_called_once_with("admin@example.test", "private password")
    selected, other = (client, admin) if role == "client" else (admin, client)
    selected.assert_called_once_with(principal)
    other.assert_not_called()


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (AuthenticationError, "Invalid email or password"),
        (DatabaseError, "Database unavailable"),
        (ValidationError, "Database configuration is invalid"),
    ],
)
def test_login_failure_can_retry(monkeypatch, capsys, error, message):
    script(monkeypatch, "", "client@example.test", "client@example.test", "0")
    login = Mock(side_effect=[error("private details"), Principal(1, "client")])
    monkeypatch.setattr(main, "authenticate", login)
    monkeypatch.setattr(main, "getpass", Mock(return_value="private password"))

    main.main()

    assert login.call_count == 2
    output = capsys.readouterr().out
    assert "Enter an email" in output
    assert message in output
    assert "Client menu" in output
    assert "private" not in output


@pytest.mark.parametrize("stage", ["exit", "email", "password", "menu"])
def test_exit_and_eof(monkeypatch, capsys, stage):
    answers = {"exit": ["0"], "email": [], "password": ["email"], "menu": ["email"]}
    script(monkeypatch, *answers[stage])
    login = Mock(return_value=Principal(1, "admin"))
    monkeypatch.setattr(main, "authenticate", login)
    password = (
        Mock(side_effect=EOFError) if stage == "password" else Mock(return_value="pw")
    )
    monkeypatch.setattr(main, "getpass", password)

    main.main()

    assert login.call_count == (1 if stage == "menu" else 0)
    assert "Goodbye" in capsys.readouterr().out


def test_menu_recovers_without_advertising_unimplemented_features(monkeypatch, capsys):
    answers = iter(["email", "?", " 0 "])
    prompts = []

    def read(prompt):
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr("builtins.input", read)
    monkeypatch.setattr(main, "authenticate", Mock(return_value=Principal(1, "admin")))
    monkeypatch.setattr(main, "getpass", Mock(return_value="pw"))

    main.main()

    output = capsys.readouterr().out
    assert "Administrator menu" in output
    assert "Invalid choice" in output
    assert (
        prompts[1:]
        == [
            "1. Add screening\n2. View schedule\n3. View remaining capacity\n0. Exit\nChoice: "
        ]
        * 2
    )


def test_password_echo_fallback_is_refused(monkeypatch, capsys):
    script(monkeypatch, "email")
    login = Mock()
    monkeypatch.setattr(main, "authenticate", login)

    def warn(_prompt):
        warnings.warn("password input would echo", GetPassWarning, stacklevel=2)
        pytest.fail("Password fallback must stop before reading")

    monkeypatch.setattr(main, "getpass", warn)
    main.main()

    login.assert_not_called()
    assert "Cannot read a hidden password" in capsys.readouterr().out


def test_module_entry_point_exits():
    result = subprocess.run(
        [sys.executable, "-m", "src.main"],
        input="0\n",
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    assert "Email" in result.stdout
    assert "Goodbye" in result.stdout
    assert not result.stderr
