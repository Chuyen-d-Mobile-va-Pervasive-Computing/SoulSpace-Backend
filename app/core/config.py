from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    DATABASE_NAME: str
    JWT_SECRET_KEY: str
    ALLOWED_ORIGINS: str
    SENTIMENT_MODEL: str = "roberta"  # default
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ASSEMBLYAI_API_KEY: str
    
    # ===== CLOUDINARY =====
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    # File size limits
    MAX_AVATAR_SIZE: int = 2 * 1024 * 1024  # 2MB
    MAX_CERTIFICATE_SIZE: int = 5 * 1024 * 1024  # 5MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()