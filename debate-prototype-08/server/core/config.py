from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Azure OpenAI 설정
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT: str
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str
    AZURE_OPENAI_API_VERSION: str

    # Langfuse 설정
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_HOST: str

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Debate Arena API"

    # CORS 설정
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # SQLite 데이터베이스 설정
    DB_PATH: str = "history.db"
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///./{DB_PATH}"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


# 설정 인스턴스 생성
settings = Settings()
