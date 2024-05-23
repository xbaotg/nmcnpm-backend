from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import os


env_file = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_file)


print(os.environ)


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

    model_config = SettingsConfigDict(env_file=env_file, env_file_encoding="utf-8")


config = Settings()  # type: ignore
