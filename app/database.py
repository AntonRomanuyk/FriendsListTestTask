import os

from config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = (
    f'postgresql://{settings.database_user}:{settings.database_password}'
    f'@{settings.database_hostname}:{settings.database_port}/{settings.database_name}'
)


# Avoid importing psycopg2 during tests; use in-memory SQLite under pytest
try:
    if os.getenv("PYTEST_CURRENT_TEST"):
        engine = create_engine("sqlite://")
    else:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
except ModuleNotFoundError:
    # Fallback when postgres driver isn't installed (e.g., during tests)
    engine = create_engine("sqlite://")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
