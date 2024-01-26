import os

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
db_file_path = os.path.join(current_dir, os.getenv("DB_FILE_PATH"))

class Config(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = os.getenv("DEBUG")
    APP_HOST: str = os.getenv("APP_HOST")
    APP_PORT: int = os.getenv("APP_PORT")
    WRITER_DB_URL: str = os.getenv("WRITER_DB_URL")
    READER_DB_URL: str = os.getenv("READER_DB_URL")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    SENTRY_SDN: str = os.getenv("SENTRY_SDN")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL")
    CELERY_BACKEND_URL: str = os.getenv("CELERY_BACKEND_URL")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME")
    DATABASE_USER: str = os.getenv("DATABASE_USER")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST")
    DATABASE_PORT: int = os.getenv("DATABASE_PORT")
    EMAIL_PORT : int = os.getenv("EMAIL_PORT")
    EMAIL_HOST_USER: str = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD : str = os.getenv("EMAIL_HOST_PASSWORD")
    USER_INFO_URL : str =  os.getenv("USER_INFO_URL")
    TOKEN_URL : str = os.getenv("TOKEN_URL")
    REDIRECT_URI : str = os.getenv("REDIRECT_URI")
    CLIENT_SECRET: str = os.getenv("CLIENT_SECRET")
    CLIENT_ID : str = os.getenv("CLIENT_ID")
    

class DevelopmentConfig(Config):
    WRITER_DB_URL: str = os.getenv("WRITER_DB_URL")
    READER_DB_URL: str = os.getenv("READER_DB_URL")


class LocalConfig(Config):
    WRITER_DB_URL: str = os.getenv("WRITER_DB_URL")
    READER_DB_URL: str = os.getenv("READER_DB_URL")


class ProductionConfig(Config):
    DEBUG: str = False
    WRITER_DB_URL: str = os.getenv("WRITER_DB_URL")
    READER_DB_URL: str = os.getenv("READER_DB_URL")


def get_config():
    env = os.getenv("ENV", "local")
    config_type = {
        "dev": DevelopmentConfig(),
        "local": LocalConfig(),
        "prod": ProductionConfig(),
    }
    return config_type["prod"]


config: Config = get_config()
