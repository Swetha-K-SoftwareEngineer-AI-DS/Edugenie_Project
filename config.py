import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Settings(BaseSettings):
    APP_NAME: str = "EduGenie – AI Educational Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Gemini AI Config
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemma-4-31b-it")
    
    # Database Config
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://root:password@localhost:3306/edugenie_db"
    )
    ALLOW_SQLITE_FALLBACK: bool = os.getenv("ALLOW_SQLITE_FALLBACK", "True").lower() in ("true", "1", "yes")
    SQLITE_URL: str = f"sqlite:///{BASE_DIR / 'edugenie.db'}"
    
    # Security Config
    SECRET_KEY: str = os.getenv("SECRET_KEY", "edugenie_super_secret_jwt_key_development_2026")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Rate Limiting
    RATE_LIMIT_AI: str = os.getenv("RATE_LIMIT_AI", "30/minute")
    
    # Server Config
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    class Config:
        case_sensitive = True
        extra = "ignore"


settings = Settings()
