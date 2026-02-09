from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LLMinate"
    db_url: str = "sqlite:///./app.db"
    local_auth_token: str = "local-dev"
    suggest_only_default: bool = True
    
    # AI Keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file="../.env",  # Look for .env in the project root (one level up from backend/)
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
