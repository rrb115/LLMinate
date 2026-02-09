from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AI Call Optimizer"
    db_url: str = "sqlite:///./app.db"
    local_auth_token: str = "local-dev"
    suggest_only_default: bool = True


settings = Settings()
