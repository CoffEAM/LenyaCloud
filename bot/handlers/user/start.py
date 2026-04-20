from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.config import load_config
from bot.database.users import upsert_user
from bot.keyboards.user_menu import get_main_menu


router = Router(name=__name__)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if message.from_user is None:
        return

    config = load_config()
    is_admin = message.from_user.id in config.tg_bot.admins

    upsert_user(message.from_user, is_admin=is_admin)

    await message.answer(
        "Добро пожаловать в VPN-бот.\n\n"
        "Через меню ниже можно отправить заявку, посмотреть подписку или написать в поддержку.\n"
        "Если VPN не работает и Telegram недоступен, можно воспользоваться VK:\n"
        f"{config.links.vk_group_link}",
        reply_markup=get_main_menu()
    )