from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI"
    default_model: str = ""
    request_timeout_seconds: int = 30
    provider_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
