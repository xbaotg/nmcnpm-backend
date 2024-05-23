from pydantic_settings import BaseSettings
from dotenv import load_dotenv, find_dotenv
import os


load_dotenv(find_dotenv(".env"))
print(os.environ["POSTGRES_SERVER"])
input()


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

    # model_config = SettingsConfigDict(env_file=env_file, env_file_encoding="utf-8")


config = Settings()  # type: ignore
