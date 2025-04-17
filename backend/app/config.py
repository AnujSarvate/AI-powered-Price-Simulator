from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./price_simulator.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    artifacts_dir: str = "./artifacts"
    app_version: str = "0.1.0"


settings = Settings()
