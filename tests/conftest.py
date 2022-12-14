import asyncio
import os
import sys

import pytest
import pytest_asyncio
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage

import db
from routers import router
from tests.mocked_bot import MockedBot
import shutil


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


@pytest.fixture(scope='session', autouse=True)
def db_close():
    try:
        yield db.check_db_exists()
    finally:
        db.conn.close()
        shutil.rmtree(db.db_dir)




