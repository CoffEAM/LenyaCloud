import asyncio
import logging
from typing import Any

import aiohttp
import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from vk_bot.config import load_vk_config
from vk_bot.database import VkDatabase


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)

config = load_vk_config()
db = VkDatabase(config.db_path)
db.init_vk_tables()

support_waiting_users: dict[int, str] = {}


def get_main_keyboard() -> str:
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Статус сервера", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Поддержка", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Частые проблемы", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("Мои обращения", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def get_support_topics_keyboard() -> str:
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("VPN на ПК", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("VPN на телефоне", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Продление подписки", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("Новый ключ", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("Другое", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def get_faq_keyboard() -> str:
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Проблемы на ПК", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Проблемы на телефоне", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("Общие вопросы", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def format_server_status(status_code: str, status_text: str) -> str:
    if status_code == "maintenance":
        title = "Статус сервера: технические работы"
    elif status_code == "issues":
        title = "Статус сервера: есть известные проблемы"
    else:
        title = "Статус сервера: работает"

    return f"{title}\n\n{status_text}"


async def notify_telegram_admins(text: str) -> None:
    if not config.tg_admins or not config.tg_bot_token:
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


async def send_message(vk_api_method: Any, user_id: int, text: str, keyboard: str | None = None) -> None:
    payload = {
        "user_id": user_id,
        "message": text,
        "random_id": 0,
    }
    if keyboard:
        payload["keyboard"] = keyboard

    await asyncio.to_thread(vk_api_method.messages.send, **payload)


async def get_full_name(vk_api_method: Any, user_id: int) -> str:
    users = await asyncio.to_thread(vk_api_method.users.get, user_ids=user_id)
    if not users:
        return f"VK user {user_id}"

    user = users[0]
    return f"{user['first_name']} {user['last_name']}".strip()


async def handle_text(vk_api_method: Any, user_id: int, text: str) -> None:
    clean_text = (text or "").strip()

    if clean_text.lower() in {"начать", "/start", "start"}:
        await send_message(
            vk_api_method,
            user_id,
            "Привет. Это резервный бот поддержки LenyaCloud во ВКонтакте.\n\n"
            "Если Telegram недоступен из-за проблем с VPN, можешь написать сюда.",
            get_main_keyboard(),
        )
        return

    if clean_text == "Статус сервера":
        status = db.get_server_status()
        await send_message(
            vk_api_method,
            user_id,
            format_server_status(status["status_code"], status["status_text"]),
            get_main_keyboard(),
        )
        return

    if clean_text == "Частые проблемы":
        await send_message(
            vk_api_method,
            user_id,
            "Выбери раздел частых проблем:",
            get_faq_keyboard(),
        )
        return

    if clean_text == "Проблемы на ПК":
        await send_message(
            vk_api_method,
            user_id,
            "Частые проблемы на ПК:\n\n"
            "1. Полностью выключи и заново включи VPN\n"
            "2. Проверь, работает ли интернет без VPN\n"
            "3. Перезапусти приложение VPN\n"
            "4. Переимпортируй ключ\n"
            "5. Если не помогло — напиши в поддержку и укажи программу и ошибку",
            get_faq_keyboard(),
        )
        return

    if clean_text == "Проблемы на телефоне":
        await send_message(
            vk_api_method,
            user_id,
            "Частые проблемы на телефоне:\n\n"
            "1. Выключи и снова включи VPN\n"
            "2. Проверь интернет без VPN\n"
            "3. Перезапусти приложение\n"
            "4. Переимпортируй ссылку\n"
            "5. Если не помогло — напиши в поддержку",
            get_faq_keyboard(),
        )
        return

    if clean_text == "Общие вопросы":
        await send_message(
            vk_api_method,
            user_id,
            "Общие вопросы:\n\n"
            "1. Если текущий ключ не работает — проверь, не закончилась ли подписка\n"
            "2. Если нужна помощь с продлением — напиши в поддержку\n"
            "3. Если идут техработы — уточни статус сервера",
            get_faq_keyboard(),
        )
        return

    if clean_text == "Поддержка":
        status = db.get_server_status()
        warning = ""
        if status["status_code"] == "maintenance":
            warning = "Сейчас ведутся технические работы. Проблема может быть связана с этим.\n\n"
        elif status["status_code"] == "issues":
            warning = "Сейчас есть известные проблемы с подключением. Проблема может быть связана с этим.\n\n"

        await send_message(
            vk_api_method,
            user_id,
            warning + "Выбери тему обращения:",
            get_support_topics_keyboard(),
        )
        return

    if clean_text in {"VPN на ПК", "VPN на телефоне", "Продление подписки", "Новый ключ", "Другое"}:
        support_waiting_users[user_id] = clean_text
        await send_message(
            vk_api_method,
            user_id,
            f"Тема: {clean_text}\n\n"
            "Теперь напиши одним следующим сообщением свою проблему. Оно уйдет в поддержку.",
            get_main_keyboard(),
        )
        return

    if clean_text == "Мои обращения":
        tickets = db.get_user_tickets(user_id)

        if not tickets:
            await send_message(
                vk_api_method,
                user_id,
                "У тебя пока нет обращений.",
                get_main_keyboard(),
            )
            return

        lines = ["Твои обращения:\n"]
        for ticket in tickets:
            topic = ticket["topic"] or "Без темы"
            lines.append(
                f"#{ticket['id']} | {topic} | {ticket['status']} | {ticket['created_at']}"
            )

        await send_message(
            vk_api_method,
            user_id,
            "\n".join(lines),
            get_main_keyboard(),
        )
        return

    if clean_text == "Назад":
        await send_message(
            vk_api_method,
            user_id,
            "Главное меню:",
            get_main_keyboard(),
        )
        return

    if user_id in support_waiting_users:
        topic = support_waiting_users.pop(user_id)
        full_name = await get_full_name(vk_api_method, user_id)
        ticket_id = db.create_ticket(
            vk_id=user_id,
            full_name=full_name,
            topic=topic,
            text=clean_text,
        )

        admin_text = (
            f"Новое VK-обращение #{ticket_id}\n\n"
            f"Тема: {topic}\n"
            f"Пользователь: {full_name}\n"
            f"VK ID: {user_id}\n\n"
            f"Сообщение:\n{clean_text}"
        )

        await notify_telegram_admins(admin_text)

        await send_message(
            vk_api_method,
            user_id,
            f"Обращение отправлено. Номер: #{ticket_id}",
            get_main_keyboard(),
        )
        return

    await send_message(
        vk_api_method,
        user_id,
        "Не понял команду. Используй кнопки ниже.",
        get_main_keyboard(),
    )


async def run_vk_bot() -> None:
    vk_session = vk_api.VkApi(token=config.group_token)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, config.group_id)

    logger.info("VK-бот запущен")

    while True:
        try:
            for event in longpoll.listen():
                if event.type != VkBotEventType.MESSAGE_NEW:
                    continue

                if not event.from_user:
                    continue

                user_id = event.object.message["from_id"]
                text = event.object.message.get("text", "")

                await handle_text(vk, user_id, text)

        except Exception as e:
            logger.exception("Ошибка в VK-боте: %s", e)
            await asyncio.sleep(3)