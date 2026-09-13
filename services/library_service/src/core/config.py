from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator



class Settings(BaseSettings):
    APP_NAME: str = "Library Service"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on", "debug")
        return bool(v)



    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/library_db",
        description="Async SQLAlchemy database URL (e.g. PostgreSQL or SQLite for tests)"
    )

    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_RESERVATIONS: str = "book-reservations"
    KAFKA_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
    )


settings = Settings()

