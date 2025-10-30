import os
import shutil
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch
from config import settings
from database import Base
from database import get_db
from fastapi.testclient import TestClient
from main import app
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
TEST_FILE_DIR = Path(__file__).resolve().parent
TEST_MEDIA_DIR = TEST_FILE_DIR / "test_media"

DUMMY_IMAGE_NAME = "test_image.jpg"
DUMMY_IMAGE_PATH = TEST_MEDIA_DIR / DUMMY_IMAGE_NAME


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_session():
    mp = MonkeyPatch()
    mp.setattr(settings, "AVATAR_DIR", TEST_MEDIA_DIR)
    mp.setattr(settings, "AVATAR_URL_PREFIX", "/media")
    os.makedirs(TEST_MEDIA_DIR, exist_ok=True)
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(DUMMY_IMAGE_PATH, 'JPEG')
    Base.metadata.create_all(bind=engine)

    yield

    mp.undo()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    db_path = TEST_FILE_DIR / "test.db"
    if db_path.exists():
        os.remove(db_path)
    if TEST_MEDIA_DIR.exists():
        shutil.rmtree(TEST_MEDIA_DIR)


@pytest.fixture(scope="function")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as c:
        yield c


def test_create_friend_missing_required_fields(client):
    response = client.post("/friends", data={
        "name": "Test User",
        "profession": "Tester"
    })
    assert response.status_code == 422
    with open(DUMMY_IMAGE_PATH, "rb") as f:
        files = {"photo": (DUMMY_IMAGE_NAME, f, "image/jpeg")}
        data = {"profession": "Tester"}
        response = client.post("/friends", data=data, files=files)
        assert response.status_code == 422
    with open(DUMMY_IMAGE_PATH, "rb") as f:
        files = {"photo": (DUMMY_IMAGE_NAME, f, "image/jpeg")}
        data = {"name": "Test User"}
        response = client.post("/friends", data=data, files=files)
        assert response.status_code == 422


def test_create_friend_success(client):
    with open(DUMMY_IMAGE_PATH, "rb") as f:
        files = {"photo": (DUMMY_IMAGE_NAME, f, "image/jpeg")}
        data = {
            "name": "Alice",
            "profession": "Data Scientist",
            "profession_description": "Works on ML pipelines"
        }
        response = client.post("/friends", data=data, files=files)
    assert response.status_code == 201  # HTTP_201_CREATED
    json_data = response.json()
    assert json_data["name"] == "Alice"
    assert json_data["profession"] == "Data Scientist"
    assert json_data["id"] is not None
    assert "photo_url" in json_data
    assert json_data["photo_url"].startswith(settings.AVATAR_URL_PREFIX)
    filename = json_data["photo_url"].split('/')[-1]
    saved_file_path = os.path.join(TEST_MEDIA_DIR, filename)
    assert os.path.exists(saved_file_path)


def test_get_friends_list(client):
    response = client.get("/friends")
    assert response.status_code == 200
    assert response.json() == []
    with open(DUMMY_IMAGE_PATH, "rb") as f:
        files = {"photo": (DUMMY_IMAGE_NAME, f, "image/jpeg")}
        data = {"name": "Bob", "profession": "Builder"}
        client.post("/friends", data=data, files=files)
    response = client.get("/friends")
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data, list)
    assert len(json_data) == 1
    assert json_data[0]["name"] == "Bob"
    assert json_data[0]["profession"] == "Builder"


def test_get_friend_by_id(client):
    with open(DUMMY_IMAGE_PATH, "rb") as f:
        files = {"photo": (DUMMY_IMAGE_NAME, f, "image/jpeg")}
        data = {"name": "Charlie", "profession": "Chef"}
        create_response = client.post("/friends", data=data, files=files)

    friend_id = create_response.json()["id"]

    response = client.get(f"/friends/{friend_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["name"] == "Charlie"
    assert json_data["id"] == friend_id
    response_404 = client.get("/friends/9999")
    assert response_404.status_code == 404

