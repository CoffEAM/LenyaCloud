from aiogram import Bot

from bot.database.users import get_all_active_users


async def broadcast_message(bot: Bot, text: str) -> tuple[int, int]:
    users = get_all_active_users()

    sent_count = 0
    failed_count = 0

    for user in users:
        try:
            await bot.send_message(user["telegram_id"], text)
            sent_count += 1
        except Exception:
            failed_count += 1

    return sent_count, failed_count