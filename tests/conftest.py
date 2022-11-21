import asyncio

import pytest
import pytest_asyncio
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

from routers import router
from tests.mocked_bot import MockedBot


@pytest_asyncio.fixture(scope='session')
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


@pytest_asyncio.fixture(scope='session')
async def dispatcher():
    dp = Dispatcher()
    dp.include_router(router=router)
    await dp.emit_startup()
    try:
        yield dp
    finally:
        await dp.emit_shutdown()


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


