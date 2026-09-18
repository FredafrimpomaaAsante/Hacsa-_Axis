from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "HACSA AXIS"
    app_env: str = "development"
    secret_key: str = "dev-only-change-me"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    database_url: str = "mysql+pymysql://hacsa:hacsa@127.0.0.1:3306/hacsa_smart_ops"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    seed_admin_email: str = "admin@hacsa10.example.com"
    seed_admin_password: str = "Admin123!"
    auto_create_tables: bool = Field(default=True)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
