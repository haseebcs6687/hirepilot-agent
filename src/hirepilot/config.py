"""Configuration loading and validation for HirePilot using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Environment
    app_env: str = Field(default="development", description="Application environment: development, testing, production")
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    database_url: str = Field(default="sqlite:///hirepilot.db", description="Database connection URL")

    # Safety & Execution Controls
    dry_run: bool = Field(default=True, description="When true, emails are drafted but never dispatched")
    autopilot: bool = Field(default=False, description="When true, background pipeline runs automatically")
    kill_switch: bool = Field(default=False, description="Master circuit breaker to halt all pipeline operations")

    # LLM Provider: Google Gemini (Primary)
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-1.5-flash", description="Gemini model name")
    gemini_rpm_limit: int = Field(default=15, description="Gemini free tier requests-per-minute limit")

    # LLM Provider: Groq (Fallback)
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
    groq_model: str = Field(default="llama-3.3-70b-versatile", description="Groq model name")
    groq_rpm_limit: int = Field(default=30, description="Groq free tier requests-per-minute limit")

    # Profile & Candidate Assets (in git-ignored private/ folder)
    profile_dir: Path = Field(default=Path("private"), description="Directory containing user profile files")
    profile_file: Path = Field(default=Path("private/profile.yaml"), description="Path to profile.yaml")
    cv_file: Path = Field(default=Path("private/cv.md"), description="Path to candidate CV markdown")
    writing_samples_dir: Path = Field(
        default=Path("private/writing_samples"), description="Directory containing tone writing samples"
    )

    # Gmail Integration
    gmail_credentials_path: Path = Field(
        default=Path("private/credentials.json"), description="Path to Gmail OAuth client secret"
    )
    gmail_token_path: Path = Field(
        default=Path("private/token.json"), description="Path to Gmail OAuth token storage"
    )
    gmail_sender_email: Optional[str] = Field(default=None, description="Sender Gmail address")

    # Deliverability & Safeguards
    daily_send_cap: int = Field(default=5, description="Maximum emails allowed to be sent per calendar day")
    min_send_delay_seconds: int = Field(default=180, description="Minimum random delay between sends")
    max_send_delay_seconds: int = Field(default=600, description="Maximum random delay between sends")
    working_hours_start: str = Field(default="09:00", description="HH:MM start of allowed sending window")
    working_hours_end: str = Field(default="17:00", description="HH:MM end of allowed sending window")
    working_timezone: str = Field(default="UTC", description="Timezone for working hours evaluation")
    working_days: str = Field(
        default="0,1,2,3,4", description="Comma-separated weekday numbers (0=Mon, 6=Sun) allowed for sending"
    )

    # Service Bindings
    api_host: str = Field(default="127.0.0.1", description="FastAPI host binding")
    api_port: int = Field(default=8000, description="FastAPI port binding")
    dashboard_port: int = Field(default=8501, description="Streamlit dashboard port")

    @property
    def parsed_working_days(self) -> set[int]:
        """Return set of integer weekdays allowed for sending."""
        try:
            return {int(day.strip()) for day in self.working_days.split(",") if day.strip()}
        except ValueError:
            return {0, 1, 2, 3, 4}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    return Settings()
