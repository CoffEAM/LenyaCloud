from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
)

from bot.config import load_config


async def set_bot_commands(bot: Bot) -> None:
    config = load_config()

    user_commands = [
        BotCommand(command="start", description="Запустить бота"),
    ]

    await bot.set_my_commands(
        commands=user_commands,
        scope=BotCommandScopeAllPrivateChats(),
    )

    admin_commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="requests", description="Заявки на ключи"),
        BotCommand(command="tickets", description="Обращения в поддержку"),
        BotCommand(command="addsub", description="Добавить подписку вручную"),
        BotCommand(command="setstatus", description="Изменить статус сервера"),
        BotCommand(command="notify", description="Разослать уведомление"),
        BotCommand(command="cancel", description="Отменить текущее действие"),
    ]

    for admin_id in config.tg_bot.admins:
        await bot.set_my_commands(
            commands=admin_commands,
            scope=BotCommandScopeChat(chat_id=admin_id),
        )