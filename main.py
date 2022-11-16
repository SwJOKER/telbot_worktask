import asyncio
import os
import logging
from routers import router
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage


TOKEN = '5726254999:AAFWfN8ZgDkQW98XCeMQD2wvqNuk0Y7rNlc'

async def main():
    bot = Bot(TOKEN, parse_mode='HTML')
    logging.basicConfig(level="INFO")
    dp = Dispatcher(storage=MemoryStorage())
    router.bot = bot
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    asyncio.run(main())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
