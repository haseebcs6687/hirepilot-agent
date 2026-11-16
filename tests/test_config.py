"""Unit tests for configuration loading and validation."""

import os
from hirepilot.config import Settings


def test_default_settings():
    """Verify default safety values: dry_run=True, autopilot=False, kill_switch=False."""
    settings = Settings()
    assert settings.dry_run is True
    assert settings.autopilot is False
    assert settings.kill_switch is False
    assert settings.daily_send_cap == 5
    assert settings.gemini_rpm_limit == 15
    assert settings.groq_rpm_limit == 30
    assert 0 in settings.parsed_working_days
    assert 4 in settings.parsed_working_days


def test_settings_env_override(monkeypatch):
    """Verify environment variables override defaults."""
    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("DAILY_SEND_CAP", "10")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()
    assert settings.dry_run is False
    assert settings.daily_send_cap == 10
    assert settings.log_level == "DEBUG"
