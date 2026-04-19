from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import load_config
from bot.database.server_status import get_server_status, set_server_status
from bot.database.tickets import (
    add_ticket_message,
    get_open_tickets,
    get_ticket_by_id,
    get_ticket_last_message,
    update_ticket_status,
)
from bot.keyboards.support import get_admin_ticket_actions
from bot.services.broadcast import broadcast_message
from bot.states.support import AdminSupportStates


router = Router(name=__name__)


def is_admin(user_id: int) -> bool:
    return user_id in load_config().tg_bot.admins


def format_ticket_card(ticket: dict, last_message: dict | None) -> str:
    username = f"@{ticket['username']}" if ticket["username"] else "без username"
    full_name = ticket["full_name"] or ticket["first_name"] or "Без имени"
    last_text = last_message["text"] if last_message else "Нет сообщений"
    topic = ticket["topic"] or "Без темы"

    return (
        f"Обращение #{ticket['id']}\n\n"
        f"Тема: {topic}\n"
        f"Пользователь: {full_name}\n"
        f"Username: {username}\n"
        f"Telegram ID: {ticket['telegram_id']}\n"
        f"Статус: {ticket['status']}\n"
        f"Последнее сообщение:\n{last_text}"
    )


@router.message(Command("tickets"))
async def show_tickets(message: Message) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        return

    tickets = get_open_tickets()

    if not tickets:
        await message.answer("Открытых обращений нет.")
        return

    await message.answer(f"Найдено обращений: {len(tickets)}")

    for ticket in tickets:
        last_message = get_ticket_last_message(ticket["id"])
        await message.answer(
            format_ticket_card(ticket, last_message),
            reply_markup=get_admin_ticket_actions(ticket["id"], ticket["status"])
        )


@router.callback_query(F.data.startswith("admin_ticket_take_"))
async def take_ticket(callback: CallbackQuery, bot: Bot) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    ticket_id = int(callback.data.rsplit("_", 1)[-1])
    ticket = get_ticket_by_id(ticket_id)

    if ticket is None:
        await callback.answer("Обращение не найдено.", show_alert=True)
        return

    update_ticket_status(ticket_id, "in_progress")

    try:
        await bot.send_message(
            ticket["telegram_id"],
            f"Твое обращение #{ticket_id} принято в работу."
        )
    except Exception:
        pass

    updated = get_ticket_by_id(ticket_id)
    last_message = get_ticket_last_message(ticket_id)

    await callback.message.edit_text(
        format_ticket_card(updated, last_message),
        reply_markup=get_admin_ticket_actions(ticket_id, updated["status"])
    )
    await callback.answer("Обращение взято в работу")


@router.callback_query(F.data.startswith("admin_ticket_reply_"))
async def start_ticket_reply(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    ticket_id = int(callback.data.rsplit("_", 1)[-1])
    ticket = get_ticket_by_id(ticket_id)

    if ticket is None:
        await callback.answer("Обращение не найдено.", show_alert=True)
        return

    await state.clear()
    await state.set_state(AdminSupportStates.entering_reply)
    await state.update_data(ticket_id=ticket_id)

    await callback.message.answer(
        f"Введи ответ пользователю по обращению #{ticket_id}.\n\nДля отмены напиши /cancel"
    )
    await callback.answer()


@router.message(AdminSupportStates.entering_reply)
async def process_ticket_reply(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await state.clear()
        return

    text = (message.text or "").strip()

    if not text:
        await message.answer("Ответ не должен быть пустым.")
        return

    if len(text) > 2000:
        await message.answer("Ответ слишком длинный.")
        return

    data = await state.get_data()
    ticket_id = data.get("ticket_id")

    if not ticket_id:
        await message.answer("Не удалось определить обращение.")
        await state.clear()
        return

    ticket = get_ticket_by_id(ticket_id)
    if ticket is None:
        await message.answer("Обращение не найдено.")
        await state.clear()
        return

    try:
        await bot.send_message(
            ticket["telegram_id"],
            f"Ответ по обращению #{ticket_id}:\n\n{text}"
        )
    except Exception as e:
        await message.answer(
            "Не удалось отправить ответ пользователю.\n"
            f"Ошибка: {e}"
        )
        return

    add_ticket_message(ticket_id, "admin", text)
    update_ticket_status(ticket_id, "in_progress")

    await message.answer(f"Ответ по обращению #{ticket_id} отправлен.")
    await state.clear()


@router.callback_query(F.data.startswith("admin_ticket_close_"))
async def close_ticket(callback: CallbackQuery, bot: Bot) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    ticket_id = int(callback.data.rsplit("_", 1)[-1])
    ticket = get_ticket_by_id(ticket_id)

    if ticket is None:
        await callback.answer("Обращение не найдено.", show_alert=True)
        return

    update_ticket_status(ticket_id, "closed")

    try:
        await bot.send_message(
            ticket["telegram_id"],
            f"Твое обращение #{ticket_id} закрыто.\n\nЕсли проблема повторится, создай новое обращение."
        )
    except Exception:
        pass

    updated = get_ticket_by_id(ticket_id)
    last_message = get_ticket_last_message(ticket_id)

    await callback.message.edit_text(
        format_ticket_card(updated, last_message),
        reply_markup=get_admin_ticket_actions(ticket_id, updated["status"])
    )
    await callback.answer("Обращение закрыто")


@router.message(Command("setstatus"))
async def set_status_command(message: Message, bot: Bot) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        return

    parts = (message.text or "").split(maxsplit=2)

    if len(parts) < 2:
        status = get_server_status()
        await message.answer(
            "Использование:\n"
            "/setstatus ok Текст\n"
            "/setstatus maintenance Текст\n"
            "/setstatus issues Текст\n\n"
            f"Сейчас: {status['status_code']} | {status['status_text']}"
        )
        return

    status_code = parts[1].strip().lower()
    status_text = parts[2].strip() if len(parts) > 2 else ""

    if status_code not in ("ok", "maintenance", "issues"):
        await message.answer("Допустимые статусы: ok, maintenance, issues")
        return

    if not status_text:
        if status_code == "ok":
            status_text = "Сервер работает в обычном режиме."
        elif status_code == "maintenance":
            status_text = "Сейчас ведутся технические работы."
        else:
            status_text = "Сейчас есть известные проблемы с подключением."

    set_server_status(status_code, status_text)

    if status_code == "ok":
        notify_text = (
            "Обновление статуса сервера\n\n"
            "Статус: работает\n"
            f"{status_text}"
        )
    elif status_code == "maintenance":
        notify_text = (
            "Обновление статуса сервера\n\n"
            "Статус: технические работы\n"
            f"{status_text}"
        )
    else:
        notify_text = (
            "Обновление статуса сервера\n\n"
            "Статус: есть проблемы\n"
            f"{status_text}"
        )

    sent_count, failed_count = await broadcast_message(bot, notify_text)

    await message.answer(
        f"Статус обновлен: {status_code}\n"
        f"{status_text}\n\n"
        f"Рассылка завершена.\n"
        f"Успешно: {sent_count}\n"
        f"Не доставлено: {failed_count}"
    )


@router.message(Command("notify"))
async def notify_command(message: Message, bot: Bot) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        return

    parts = (message.text or "").split(maxsplit=1)

    if len(parts) < 2 or not parts[1].strip():
        await message.answer(
            "Использование:\n"
            "/notify Текст уведомления"
        )
        return

    notify_text = parts[1].strip()

    sent_count, failed_count = await broadcast_message(bot, notify_text)

    await message.answer(
        "Уведомление отправлено.\n\n"
        f"Успешно: {sent_count}\n"
        f"Не доставлено: {failed_count}"
    )


@router.message(Command("cancel"))
async def cancel_admin_support(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state != AdminSupportStates.entering_reply.state:
        return

    await state.clear()
    await message.answer("Ответ на обращение отменен.")