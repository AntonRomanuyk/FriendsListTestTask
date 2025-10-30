from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from config import settings
from pytest_httpx import HTTPXMock

from bot import NAME
from bot import PHOTO
from bot import PROFESSION
from bot import add_friend_start
from bot import get_name
from bot import get_photo
from bot import list_friends
from bot import start

settings.BACKEND_BASE_URL = "http://test-api"

pytestmark = pytest.mark.asyncio


async def test_start_command():
    update = Mock()

    update.message.reply_text = AsyncMock()

    context = Mock()

    await start(update, context)

    update.message.reply_text.assert_called_once_with(
        "Hi! I'm your bot for managing your friend list.\n\n"
        "Available commands:\n"
        "/addfriend - add a new friend\n"
        "/list - show all friends\n"
        "/friend <id> - show a friend by ID"
    )


async def test_list_friends_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.BACKEND_BASE_URL}/friends/",
        json=[
            {"name": "Alice", "profession": "Tester", "photo_url": "/media/alice.jpg"},
            {"name": "Bob", "profession": "Dev", "photo_url": "/media/bob.jpg"}
        ],
        status_code=200
    )

    update = Mock()
    update.message.reply_text = AsyncMock()
    context = Mock()

    await list_friends(update, context)

    final_call_args = update.message.reply_text.call_args_list[1]
    final_reply_text = final_call_args.args[0]
    final_parse_mode = final_call_args.kwargs['parse_mode']

    assert final_parse_mode == 'MarkdownV2'
    assert "Here are your friends:" in final_reply_text
    assert "👤 *Alice*" in final_reply_text
    assert "💼 **Profession:** Tester" in final_reply_text

    expected_url_alice = "🖼️ *Photo URL:* `(/media/alice\\.jpg)`"
    assert expected_url_alice in final_reply_text
    assert "👤 *Bob*" in final_reply_text
    assert "💼 **Profession:** Dev" in final_reply_text

    expected_url_bob = "🖼️ *Photo URL:* `(/media/bob\\.jpg)`"
    assert expected_url_bob in final_reply_text


async def test_list_friends_api_fail(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.BACKEND_BASE_URL}/friends/",
        status_code=500
    )

    update = Mock()
    update.message.reply_text = AsyncMock()
    context = Mock()

    await list_friends(update, context)

    error_reply = update.message.reply_text.call_args_list[1].args[0]
    assert "Failed to get friend list" in error_reply


async def test_conversation_flow():
    context = Mock()
    context.user_data = {}

    update_start = Mock()
    update_start.message.reply_text = AsyncMock()

    next_state = await add_friend_start(update_start, context)

    update_start.message.reply_text.assert_called_with(
        "Let's start creating a friend. Please send me their photo.\n\n"
        "Send /cancel to stop at any time."
    )
    assert next_state == PHOTO

    update_photo = Mock()
    update_photo.message.photo = [Mock()]
    update_photo.message.photo[-1].get_file = AsyncMock()
    update_photo.message.photo[-1].get_file.return_value.download_as_bytearray = AsyncMock(
        return_value=b"fake_image_bytes"
    )
    update_photo.message.reply_text = AsyncMock()

    next_state = await get_photo(update_photo, context)

    assert context.user_data['friend_photo'] == b"fake_image_bytes"

    update_photo.message.reply_text.assert_called_with("Great photo! Now, enter the friend's name:")

    assert next_state == NAME

    update_name = Mock()
    update_name.message.text = "Test Friend"
    update_name.message.reply_text = AsyncMock()

    next_state = await get_name(update_name, context)

    assert context.user_data['friend_name'] == "Test Friend"

    update_name.message.reply_text.assert_called_with("Got it. Now, enter their profession:")
    assert next_state == PROFESSION
