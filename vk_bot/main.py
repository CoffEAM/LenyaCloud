import asyncio
import logging
from typing import Final

import aiohttp
from vkbottle.bot import Bot, Message

from vk_bot.config import load_vk_config
from vk_bot.database import VkDatabase
from vk_bot.keyboards import (
    get_faq_keyboard,
    get_main_keyboard,
    get_support_topic_keyboard,
)
from vk_bot.texts import (
    format_server_status,
    get_common_faq_text,
    get_pc_faq_text,
    get_phone_faq_text,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)

config = load_vk_config()
db = VkDatabase(config.db_path)
db.init_vk_tables()

bot = Bot(config.group_token)

# Память для незавершенного шага поддержки
# user_id -> topic
support_waiting_users: dict[int, str] = {}

SUPPORT_TOPICS: Final[set[str]] = {
    "VPN на ПК",
    "VPN на телефоне",
    "Продление подписки",
    "Новый ключ",
    "Другое",
}


async def get_vk_full_name(user_id: int) -> str:
    users = await bot.api.users.get(user_ids=[user_id])
    if not users:
        return f"VK user {user_id}"

    user = users[0]
    first_name = getattr(user, "first_name", "") or ""
    last_name = getattr(user, "last_name", "") or ""
    full_name = f"{first_name} {last_name}".strip()
    return full_name or f"VK user {user_id}"


async def notify_telegram_admins(text: str) -> None:
    if not config.tg_admins:
        logger.error("Список TG-админов пуст")
        return

    if not config.tg_bot_token:
        logger.error("Не найден токен TG-бота")
        return

    url = f"https://api.telegram.org/bot{config.tg_bot_token}/sendMessage"

    async with aiohttp.ClientSession() as session:
        for admin_id in config.tg_admins:
            payload = {
                "chat_id": admin_id,
                "text": text,
            }

            try:
                async with session.post(url, data=payload, timeout=15) as response:
                    response_text = await response.text()
                    logger.info(
                        "TG notify admin_id=%s status=%s response=%s",
                        admin_id,
                        response.status,
                        response_text,
                    )
            except Exception as e:
                logger.exception("Не удалось отправить уведомление админу %s: %s", admin_id, e)


@bot.on.private_message(text=["Начать", "start", "/start"])
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет. Это резервный бот поддержки LenyaCloud во ВКонтакте.\n\n"
        "Если Telegram недоступен из-за проблем с VPN, можешь написать сюда.",
        keyboard=get_main_keyboard(),
    )


@bot.on.private_message(text="Статус сервера")
async def server_status_handler(message: Message) -> None:
    status = db.get_server_status()

    await message.answer(
        format_server_status(status["status_code"], status["status_text"]),
        keyboard=get_main_keyboard(),
    )


@bot.on.private_message(text="Частые проблемы")
async def faq_handler(message: Message) -> None:
    await message.answer(
        "Выбери раздел частых проблем:",
        keyboard=get_faq_keyboard(),
    )


@bot.on.private_message(text="Проблемы на ПК")
async def faq_pc_handler(message: Message) -> None:
    await message.answer(
        get_pc_faq_text(),
        keyboard=get_faq_keyboard(),
    )


@bot.on.private_message(text="Проблемы на телефоне")
async def faq_phone_handler(message: Message) -> None:
    await message.answer(
        get_phone_faq_text(),
        keyboard=get_faq_keyboard(),
    )


@bot.on.private_message(text="Общие вопросы")
async def faq_common_handler(message: Message) -> None:
    await message.answer(
        get_common_faq_text(),
        keyboard=get_faq_keyboard(),
    )


@bot.on.private_message(text="Назад")
async def back_handler(message: Message) -> None:
    await message.answer(
        "Главное меню:",
        keyboard=get_main_keyboard(),
    )


@bot.on.private_message(text="Поддержка")
async def support_handler(message: Message) -> None:
    status = db.get_server_status()

    warning_text = ""
    if status["status_code"] == "maintenance":
        warning_text = (
            "Сейчас ведутся технические работы.\n"
            "Проблема может быть связана с этим.\n\n"
        )
    elif status["status_code"] == "issues":
        warning_text = (
            "Сейчас есть известные проблемы с подключением.\n"
            "Проблема может быть связана с этим.\n\n"
        )

    await message.answer(
        warning_text + "Выбери тему обращения:",
        keyboard=get_support_topic_keyboard(),
    )


@bot.on.private_message(text=["VPN на ПК", "VPN на телефоне", "Продление подписки", "Новый ключ", "Другое"])
async def choose_support_topic_handler(message: Message) -> None:
    if message.from_id is None:
        return

    topic = message.text.strip()
    support_waiting_users[message.from_id] = topic

    await message.answer(
        f"Тема: {topic}\n\n"
        "Теперь напиши одним сообщением свою проблему. Оно будет отправлено в поддержку.",
        keyboard=get_main_keyboard(),
    )


@bot.on.private_message(text="Мои обращения")
async def my_tickets_handler(message: Message) -> None:
    if message.from_id is None:
        return

    tickets = db.get_user_tickets(message.from_id)

    if not tickets:
        await message.answer(
            "У тебя пока нет обращений.",
            keyboard=get_main_keyboard(),
        )
        return

    lines: list[str] = ["Твои обращения:\n"]
    for ticket in tickets:
        topic = ticket["topic"] or "Без темы"
        lines.append(
            f"#{ticket['id']} | {topic} | {ticket['status']} | {ticket['created_at']}"
        )

    await message.answer(
        "\n".join(lines),
        keyboard=get_main_keyboard(),
    )


@bot.on.private_message()
async def generic_message_handler(message: Message) -> None:
    if message.from_id is None:
        return

    user_id = message.from_id
    text = (message.text or "").strip()

    if not text:
        await message.answer(
            "Я понимаю только текстовые сообщения.",
            keyboard=get_main_keyboard(),
        )
        return

    if user_id not in support_waiting_users:
        await message.answer(
            "Не понял команду. Используй кнопки ниже.",
            keyboard=get_main_keyboard(),
        )
        return

    topic = support_waiting_users.pop(user_id)

    full_name = await get_vk_full_name(user_id)
    ticket_id = db.create_ticket(
        vk_id=user_id,
        full_name=full_name,
        topic=topic,
        text=text,
    )

    admin_text = (
        f"Новое VK-обращение #{ticket_id}\n\n"
        f"Тема: {topic}\n"
        f"Пользователь: {full_name}\n"
        f"VK ID: {user_id}\n\n"
        f"Сообщение:\n{text}"
    )

    await notify_telegram_admins(admin_text)

    await message.answer(
        f"Обращение отправлено. Номер: #{ticket_id}",
        keyboard=get_main_keyboard(),
    )


if __name__ == "__main__":
    bot.run_forever()