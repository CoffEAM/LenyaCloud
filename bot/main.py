import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import load_config
from bot.database.db import init_db
from bot.handlers.admin.manual_subscription import router as manual_sub_router
from bot.handlers.admin.requests import router as admin_requests_router
from bot.handlers.admin.support import router as admin_support_router
from bot.handlers.user.get_key import router as get_key_router
from bot.handlers.user.menu import router as user_menu_router
from bot.handlers.user.start import router as start_router
from bot.handlers.user.support import router as user_support_router
from bot.utils.commands import set_bot_commands


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


async def main() -> None:
    config = load_config()

    init_db()

    bot = Bot(token=config.tg_bot.token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(get_key_router)
    dp.include_router(user_menu_router)
    dp.include_router(user_support_router)

    dp.include_router(admin_requests_router)
    dp.include_router(manual_sub_router)
    dp.include_router(admin_support_router)

    await set_bot_commands(bot)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")