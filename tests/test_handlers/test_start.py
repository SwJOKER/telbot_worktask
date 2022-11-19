from unittest.mock import AsyncMock

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

import keyboards
from strings import *

import pytest
from routers import cmd_start
from tests.utils import TEST_USER



@pytest.mark.asyncio
async def test_start_handler(storage, bot):
    message = AsyncMock()
    state = FSMContext(
        bot=bot,
        storage=storage,
        key=StorageKey(bot_id=bot.id, user_id=TEST_USER.id)
    )
    await cmd_start(message, state)
    message.answer.assert_called_with(STR_WELCOME, reply_markup=keyboards.union_options_kb())

