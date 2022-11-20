import pytest
from aiogram import Dispatcher, Bot

from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import SendMessage
import db

from tests.test_utils import TEST_USER, TEST_CHAT, get_message, get_update



@pytest.mark.asyncio
async def test_start_command(dispatcher: Dispatcher, bot: Bot, storage: MemoryStorage):
    db.check_db_exists()
    message = await get_message('/start')
    result: SendMessage = await dispatcher.feed_update(bot=bot, update=await get_update(message=message))
    assert isinstance(result, SendMessage)
    data = await dispatcher.storage.get_data(bot=bot, key=StorageKey(bot.id, TEST_CHAT.id, user_id=TEST_USER.id))
    assert not data



