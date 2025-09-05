from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    DATABASE_NAME: str
    JWT_SECRET_KEY: str
    ALLOWED_ORIGINS: str
    SENTIMENT_MODEL: str = "roberta"  # default

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()