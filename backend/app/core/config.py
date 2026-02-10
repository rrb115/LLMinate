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

    # Progressive certainty engine
    similarity_threshold: float = 0.78
    similarity_top_k: int = 3
    normalization_similarity_threshold: float = 0.7
    llm_enabled: bool = False
    deterministic_capable_intents: tuple[str, ...] = (
        "yes_no_classification",
        "structured_extraction",
        "small_domain_label_matching",
    )

    model_config = SettingsConfigDict(
        env_file="../.env",  # Look for .env in the project root (one level up from backend/)
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
