import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

# Опциональная загрузка .env для локальной разработки
if ENV_PATH.exists():
    content = ENV_PATH.read_text(encoding="utf-8-sig")
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())  

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH if ENV_PATH.exists() else None,
        env_file_encoding="utf-8-sig",
        extra="ignore", 
    )
    database_url: str
    
    oauth2_client_id: str | None = None
    oauth2_client_secret: str | None = None
    oauth2_authorization_url: str | None = None
    oauth2_token_url: str | None = None
    oauth2_user_info_url: str | None = None

    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_port: int = 587
    mail_server: str = ""
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    use_credentials: bool = True
    validate_certs: bool = True
    frontend_url: str = "http://localhost:3000"


settings = Settings()  # type: ignore