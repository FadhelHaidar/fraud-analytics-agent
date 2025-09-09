from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str
    groq_api_url: str
    mistral_api_key: str
    qdrant_url: str
    postgres_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()