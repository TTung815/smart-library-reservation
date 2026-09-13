from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    APP_NAME: str = "Reservation Service"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on", "debug")
        return bool(v)

    # Redis configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # Kafka configuration (for Phase 4)
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_RESERVATIONS: str = "book-reservations"
    KAFKA_GROUP_ID: str = "reservation-service-group"
    KAFKA_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
    )


settings = Settings()

