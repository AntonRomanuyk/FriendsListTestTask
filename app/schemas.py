
from pydantic import BaseModel
from pydantic import ConfigDict


class FriendBase(BaseModel):
    name: str
    profession: str
    profession_description: str | None = None


class FriendCreate(FriendBase):
    pass

class FriendOut(FriendBase):
    id: int
    photo_url: str | None = None
    model_config = ConfigDict(from_attributes=True)
