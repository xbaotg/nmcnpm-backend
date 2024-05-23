from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


env_file = Path(__file__).parent / ".env"
print(env_file)


class Settings(BaseSettings):
    SQL_INIT_PATH: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    POSTGRES_DB: str

    SECRET_KEY: str
    ALGORITHM: str

    API_PREFIX_USERS: str
    API_PREFIX_AUTH: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Settings()  # type: ignore