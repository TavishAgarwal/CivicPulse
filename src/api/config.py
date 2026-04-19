"""
CivicPulse — API Configuration

Pydantic Settings loaded from environment variables.
Validates all required vars at startup — raises descriptive error if missing.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    civicpulse_env: str = "development"
    app_name: str = "CivicPulse"
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    secret_key: str  # Required — JWT signing key

    # Database
    database_url: str  # Required
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_css_ttl_seconds: int = 3600
    redis_volunteer_ttl_seconds: int = 900
    redis_heatmap_ttl_seconds: int = 1800

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"

    # CSS Thresholds — loaded from env, never hardcoded
    css_stable_max: int = 30
    css_elevated_max: int = 55
    css_high_threshold: int = 56
    css_critical_threshold: int = 76

    # Auth
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 8

    # Dispatch
    dispatch_match_count: int = 5
    dispatch_confirm_timeout_minutes: int = 15
    dispatch_weight_proximity: float = 0.35
    dispatch_weight_skill: float = 0.30
    dispatch_weight_availability: float = 0.20
    dispatch_weight_fatigue: float = 0.15
    fatigue_increment_per_dispatch: float = 0.15
    fatigue_recovery_days: int = 2

    # Feature flags
    feature_auto_dispatch: bool = False
    feature_rlhf_layer: bool = False

    # Optional integrations
    whatsapp_api_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
    firebase_project_id: Optional[str] = None
    firebase_server_key: Optional[str] = None
    mapbox_api_key: Optional[str] = None

    # Privacy
    anonymization_k_value: int = 5
    data_retention_days_raw: int = 7
    data_retention_days_processed: int = 730

    # Rate limiting
    rate_limit_anonymous: str = "20/minute"
    rate_limit_authenticated: str = "100/minute"
    rate_limit_ingest: str = "500/minute"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Instantiate at import — raises ValidationError if required vars missing
settings = Settings()
