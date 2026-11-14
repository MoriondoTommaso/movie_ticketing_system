"""Configuration/guard tests are offline; connection tests require real MySQL."""

import pytest

from src import database

ENV = {
    "DB_HOST": "127.0.0.1",
    "DB_PORT": "3306",
    "DB_NAME": "cinema_dev",
    "DB_USER": "cinema_dev",
    "DB_PASSWORD": "fictional_dev",
    "TEST_DB_HOST": "127.0.0.1",
    "TEST_DB_PORT": "3307",
    "TEST_DB_NAME": "cinema_test",
    "TEST_DB_USER": "cinema_test",
    "TEST_DB_PASSWORD": "fictional_test",
}


def test_settings_keep_development_and_test_separate():
    dev = database.settings_from_env(target="dev", environ=ENV)
    test = database.settings_from_env(target="test", environ=ENV)
    assert (dev.name, dev.port, dev.user) == ("cinema_dev", 3306, "cinema_dev")
    assert (test.name, test.port, test.user) == ("cinema_test", 3307, "cinema_test")
    assert "fictional_test" not in repr(test)


@pytest.mark.parametrize("field", ["HOST", "PORT", "NAME", "USER", "PASSWORD"])
def test_test_settings_never_fall_back_to_development(field):
    settings = dict(ENV)
    del settings[f"TEST_DB_{field}"]
    with pytest.raises(database.ValidationError):
        database.settings_from_env(target="test", environ=settings)


@pytest.mark.parametrize("port", ["", "0", "-1", "65536", "not-a-port"])
def test_settings_reject_invalid_ports(port):
    with pytest.raises(database.ValidationError):
        database.settings_from_env(target="test", environ=ENV | {"TEST_DB_PORT": port})


def test_settings_reject_unknown_target():
    with pytest.raises(database.ValidationError):
        database.settings_from_env(target="production", environ=ENV)
