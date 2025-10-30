from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_user: str


    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_BASE_DIR: Path = BASE_DIR / "uploads"
    AVATAR_DIR: Path = UPLOAD_BASE_DIR / "avatars"
    AVATAR_URL_PREFIX: str = "/media"

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
