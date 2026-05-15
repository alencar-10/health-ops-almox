from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Vivver Almox MVP"
    APP_MODE: str = "LAB" # LAB or PRODUCTION
    
    # Vivver ERP Credentials (SECRETS - ONLY ACCESSED BY CORE)
    VIVVER_URL: str = "https://guaraciama-mg.vivver.com"
    VITE_MUNICIPALITY_ID: str = "3128253"
    VIVVER_USER: str = ""
    VIVVER_PASS: str = ""
    # ID Vivver (codoperador) para lookups Seg::Operador::ConexaoQuery — obrigatório para listagens
    VIVVER_OPERATOR_ID: str = ""
    VIVVER_AUTH_TOKEN: str = ""
    VIVVER_SESSION_ID: str = ""
    
    # Database
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int = 5434
    
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
