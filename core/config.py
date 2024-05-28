from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import find_dotenv


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=find_dotenv())

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
    API_PREFIX_PLAYERS: str
    API_PREFIX_REFEREES: str
    API_PREFIX_CLUBS: str


config = Settings()  # type: ignore
