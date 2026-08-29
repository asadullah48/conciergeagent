"""Environment parsing must be predictable and safe by default."""
from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from conciergeagent.core.config import DEFAULT_ALLOWED_ORIGINS, get_settings

_ALL_KEYS = ("ENVIRONMENT", "LOG_LEVEL", "JSON_LOGS", "ALLOWED_ORIGINS", "METRICS_ENABLED")


def test_defaults_when_environment_is_empty(monkeypatch):
    for key in _ALL_KEYS:
        monkeypatch.delenv(key, raising=False)
    settings = get_settings()
    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.json_logs is True
    assert settings.metrics_enabled is True
    assert settings.allowed_origins == DEFAULT_ALLOWED_ORIGINS


def test_default_origins_do_not_include_wildcard():
    """A credentialed API must never ship a wildcard origin by default."""
    assert "*" not in DEFAULT_ALLOWED_ORIGINS


def test_default_origins_include_the_portfolio_site():
    assert any("devunity" in origin for origin in DEFAULT_ALLOWED_ORIGINS)


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", "  True  "])
def test_truthy_boolean_values(monkeypatch, value):
    monkeypatch.setenv("JSON_LOGS", value)
    assert get_settings().json_logs is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off", "", "banana"])
def test_falsey_boolean_values(monkeypatch, value):
    monkeypatch.setenv("JSON_LOGS", value)
    assert get_settings().json_logs is False


def test_log_level_is_upcased(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "debug")
    assert get_settings().log_level == "DEBUG"


def test_origins_are_split_and_trimmed(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", " https://a.com , https://b.com ,, ")
    assert get_settings().allowed_origins == ["https://a.com", "https://b.com"]


def test_blank_origins_fall_back_to_defaults(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "   ")
    assert get_settings().allowed_origins == DEFAULT_ALLOWED_ORIGINS


def test_metrics_can_be_disabled(monkeypatch):
    monkeypatch.setenv("METRICS_ENABLED", "false")
    assert get_settings().metrics_enabled is False


@pytest.mark.parametrize(
    "value,expected",
    [("production", True), ("PROD", True), ("development", False), ("staging", False)],
)
def test_is_production_detection(monkeypatch, value, expected):
    monkeypatch.setenv("ENVIRONMENT", value)
    assert get_settings().is_production is expected


def test_settings_are_immutable():
    settings = get_settings()
    with pytest.raises(FrozenInstanceError):
        settings.environment = "hacked"  # type: ignore[misc]


def test_default_origin_list_is_not_shared_between_snapshots(monkeypatch):
    """Mutating one snapshot must not corrupt the module-level default."""
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    get_settings().allowed_origins.append("https://injected.example")
    assert "https://injected.example" not in get_settings().allowed_origins
