import os


class Settings:

    def __init__(self) -> None:
        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
        self.BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
