from pydantic_settings import BaseSettings , SettingsConfigDict


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    SCRAPINGBEE_API_KEY: str


api_settings = APISettings()