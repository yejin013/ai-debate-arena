import os
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Debate Arena API"

    # CORS 설정
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # SQLite 데이터베이스 설정
    SQLITE_DB_FILE: str = "debate_arena.db"
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///./{SQLITE_DB_FILE}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# 설정 인스턴스 생성
settings = Settings()
