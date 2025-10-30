from typing import Any

import httpx
from config import settings


async def add_friend(data: dict[str, Any], photo_bytes: bytes) -> dict[str, Any] | None:
    files = {'photo': ('friend_photo.jpg', photo_bytes, 'image/jpeg')}

    form_data = {
        'name': data['name'],
        'profession': data['profession'],
        'profession_description': data.get('profession_description', '')
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{settings.BACKEND_BASE_URL}/friends/", data=form_data, files=files)

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error when creating a friend: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Request error when creating a friend: {e}")
            return None


async def get_all_friends() -> list[dict[str, Any]] | None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.BACKEND_BASE_URL}/friends/")
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            print(f"Error while getting friends list: {e}")
            return None


async def get_friend_by_id(friend_id: int) -> dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        try:

            response = await client.get(f"{settings.BACKEND_BASE_URL}/friends/{friend_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"error": "not_found"}
            print(f"Error while getting friend: {friend_id}: {e}")
            return None
        except httpx.RequestError as e:
            print(f"Request error while getting friend {friend_id}: {e}")
            return None


async def get_photo_bytes(photo_url: str) -> bytes | None:

    url = f"{settings.BACKEND_BASE_URL}{photo_url}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            print(f"Error downloading photo {url}: {e}")
            return None
