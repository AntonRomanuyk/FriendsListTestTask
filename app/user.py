import os
import uuid
from pathlib import Path

import models
import schemas
from config import settings
from database import get_db
from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from sqlalchemy.orm import Session
from starlette.status import HTTP_201_CREATED
from starlette.status import HTTP_404_NOT_FOUND
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

router = APIRouter(
    prefix="/friends",
    tags=["Friend"]
)


@router.post("/", status_code=HTTP_201_CREATED, response_model=schemas.FriendOut)
def create_friend(
        name: str = Form(...),
        profession: str = Form(...),
        profession_description: str | None = Form(None),
        db: Session = Depends(get_db),
        photo: UploadFile = File(...)
):
    photo_url = None

    try:
        if photo and photo.filename:
            os.makedirs(settings.AVATAR_DIR, exist_ok=True)

            file_extension = Path(photo.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            file_path = os.path.join(settings.AVATAR_DIR, unique_filename)

            photo_url = f"{settings.AVATAR_URL_PREFIX}/{unique_filename}"

            with open(file_path, "wb") as buffer:
                content = photo.file.read()
                buffer.write(content)

        new_friend = models.Friend(
            name=name,
            profession=profession,
            profession_description=profession_description,
            photo_url=photo_url,
        )

        db.add(new_friend)
        db.commit()
        db.refresh(new_friend)

        return new_friend

    except Exception as e:
        db.rollback()
        print(f"Error creating friend: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) from e

@router.get("/{id}", response_model=schemas.FriendOut)
def get_friend(id: int, db: Session = Depends(get_db)):
    try:
        friend = db.query(models.Friend).filter(models.Friend.id == id).first()
        if not friend:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Friend not found")
        return friend
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR) from e


@router.get("/", response_model=list[schemas.FriendOut])
def get_friends(db: Session = Depends(get_db)):
    try:
        friends = db.query(models.Friend).all()
        return friends
    except Exception as e:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR) from e

