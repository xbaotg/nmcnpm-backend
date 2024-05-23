from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


env_file = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    model_config: SettingsConfigDict = {
        "env_file": env_file,
        "env_file_encoding": "utf-8",
    }

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


config = Settings()  # type: ignore
