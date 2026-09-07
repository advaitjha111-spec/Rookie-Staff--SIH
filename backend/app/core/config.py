from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    MAXMIND_ACCOUNT_ID: str = ""
    MAXMIND_LICENSE_KEY: str = ""
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "yourpassword"
    OLLAMA_HOST: str = "http://localhost:11434"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
