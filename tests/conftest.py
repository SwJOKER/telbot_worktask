import pytest
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

from tests.mocked_bot import MockedBot


@pytest.fixture(scope='session')
async def storage():
    storage = MemoryStorage()
    try:
        yield storage
    finally:
        await storage.close()


@pytest.fixture(scope='session')
def bot():
    bot = MockedBot()
    token = Bot.set_current(bot)
    try:
        yield bot
    finally:
        Bot.reset_current(token)


@pytest.fixture(scope='session')
async def dispatcher():
    dp = Dispatcher()
    await dp.emit_startup()
    try:
        yield dp
    finally:
        await dp.emit_shutdown()