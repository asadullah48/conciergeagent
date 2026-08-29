"""Environment-driven runtime configuration.

Deliberately stdlib-only: the platform advertises a small dependency surface,
and a settings object is not worth widening it for.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

_TRUTHY = {"1", "true", "yes", "on"}

DEFAULT_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8005",
    "http://localhost:8005",
    "https://asadullahshafique-devunity.vercel.app",
]


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    return default if raw is None else raw.strip().lower() in _TRUTHY


def _env_list(name: str, default: list[str]) -> list[str]:
    """Parse a comma-separated env var, falling back to ``default``.

    The fallback is applied to the *parsed* result, not the raw string: a
    whitespace-only value would otherwise yield an empty list and silently
    disable every allowed origin.
    """
    parsed = [item.strip() for item in (os.getenv(name) or "").split(",") if item.strip()]
    return parsed or list(default)


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of process configuration."""

    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    json_logs: bool = field(default_factory=lambda: _env_bool("JSON_LOGS", True))
    allowed_origins: list[str] = field(
        default_factory=lambda: _env_list("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    )
    metrics_enabled: bool = field(default_factory=lambda: _env_bool("METRICS_ENABLED", True))

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


def get_settings() -> Settings:
    """Build a Settings snapshot from the current environment."""
    return Settings()
