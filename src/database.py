"""Explicit MySQL settings and connections; callers own transactions/resources."""

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values

Target = Literal["dev", "test"]


class CinemaError(Exception):
    """Base for service failures safe to translate at the interface boundary."""


class ValidationError(CinemaError):
    """Invalid configuration or application input."""


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str = field(repr=False)


def settings_from_env(
    *, target: Target = "dev", environ: Mapping[str, str] | None = None
) -> DatabaseSettings:
    """Read one complete target; process settings override the repository .env."""
    if target not in ("dev", "test"):
        raise ValidationError("Unknown database target")
    if environ is None:
        environ = {
            **dotenv_values(Path(__file__).resolve().parents[1] / ".env"),
            **os.environ,
        }
    prefix = "DB" if target == "dev" else "TEST_DB"
    values = {}
    for key in ("HOST", "PORT", "NAME", "USER", "PASSWORD"):
        value = environ.get(f"{prefix}_{key}")
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"Missing {prefix}_{key}")
        values[key] = value
    if not values["PORT"].isascii() or not values["PORT"].isdecimal():
        raise ValidationError(f"Invalid {prefix}_PORT")
    port = int(values["PORT"])
    if not 1 <= port <= 65535:
        raise ValidationError(f"Invalid {prefix}_PORT")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", values["NAME"]):
        raise ValidationError(f"Invalid {prefix}_NAME")
    return DatabaseSettings(
        values["HOST"], port, values["NAME"], values["USER"], values["PASSWORD"]
    )
