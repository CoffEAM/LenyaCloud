from aiogram import F, Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import load_config
from bot.database.server_status import get_server_status
from bot.database.tickets import create_ticket, get_user_tickets
from bot.keyboards.support import (
    get_support_cancel_menu,
    get_support_faq_common_menu,
    get_support_faq_menu,
    get_support_faq_pc_menu,
    get_support_faq_phone_menu,
    get_support_main_menu,
    get_support_topic_menu,
    get_support_warning_menu,
)
from bot.keyboards.user_menu import get_main_menu
from bot.states.support import UserSupportStates


router = Router(name=__name__)


async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


def get_support_header_text() -> str:
    status = get_server_status()

    if status["status_code"] == "maintenance":
        return (
            "Поддержка.\n\n"
            "Сейчас ведутся технические работы.\n"
            f"{status['status_text']}"
        )

    if status["status_code"] == "issues":
        return (
            "Поддержка.\n\n"
            "Сейчас есть известные проблемы с подключением.\n"
            f"{status['status_text']}"
        )

    return "Поддержка.\n\nЗдесь можно найти решение частых проблем или написать обращение."


def get_status_warning_text() -> str | None:
    status = get_server_status()

    if status["status_code"] == "maintenance":
        return (
            "Сейчас ведутся технические работы.\n\n"
            f"{status['status_text']}\n\n"
            "Проблема может быть связана с этим."
        )

    if status["status_code"] == "issues":
        return (
            "Сейчас есть известные проблемы с подключением.\n\n"
            f"{status['status_text']}\n\n"
            "Проблема может быть связана с этим."
        )

    return None


def get_topic_text(topic_code: str) -> str:
    mapping = {
        "pc": "Проблема с VPN на ПК",
        "phone": "Проблема с VPN на телефоне",
        "renew": "Продление подписки",
        "key": "Новый ключ",
        "other": "Другое",
    }
    return mapping.get(topic_code, "Другое")


@router.callback_query(F.data == "menu_support")
async def support_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(
        callback,
        get_support_header_text(),
        reply_markup=get_support_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_back_main")
async def support_back_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(
        callback,
        "Главное меню:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_back_support")
async def support_back_support(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(
        callback,
        get_support_header_text(),
        reply_markup=get_support_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq")
async def support_faq(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(
        callback,
        "Частые проблемы.\n\nВыбери раздел:",
        reply_markup=get_support_faq_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_pc")
async def support_faq_pc(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Частые проблемы на ПК.\n\nВыбери проблему:",
        reply_markup=get_support_faq_pc_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_phone")
async def support_faq_phone(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Частые проблемы на телефоне.\n\nВыбери проблему:",
        reply_markup=get_support_faq_phone_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_common")
async def support_faq_common(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Общие вопросы.\n\nВыбери пункт:",
        reply_markup=get_support_faq_common_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_pc_connect")
async def faq_pc_connect(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Если VPN на ПК не подключается:\n\n"
        "1. Полностью выключи и заново включи VPN\n"
        "2. Проверь, работает ли интернет без VPN\n"
        "3. Перезапусти приложение VPN\n"
        "4. Переимпортируй ключ\n"
        "5. Если не помогло — напиши в поддержку и укажи программу, которой пользуешься",
        reply_markup=get_support_faq_pc_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_pc_sites")
async def faq_pc_sites(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Если VPN подключается, но сайты не открываются:\n\n"
        "1. Выключи и включи VPN\n"
        "2. Проверь доступ без VPN\n"
        "3. Перезапусти приложение\n"
        "4. Попробуй заново импортировать ключ\n"
        "5. Если не помогло — напиши в поддержку",
        reply_markup=get_support_faq_pc_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_pc_speed")
async def faq_pc_speed(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Если на ПК низкая скорость:\n\n"
        "1. Проверь скорость без VPN\n"
        "2. Перезапусти VPN\n"
        "3. Закрой загрузки и обновления в фоне\n"
        "4. Если проблема сохраняется — напиши в поддержку",
        reply_markup=get_support_faq_pc_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_pc_import")
async def faq_pc_import(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Если ключ не импортируется на ПК:\n\n"
        "1. Убедись, что копируешь ссылку полностью\n"
        "2. Проверь, что вставляешь ее в правильный раздел приложения\n"
        "3. Попробуй удалить лишние пробелы и пустые строки\n"
        "4. Если не помогло — напиши в поддержку",
        reply_markup=get_support_faq_pc_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_phone_connect")
async def faq_phone_connect(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Если VPN на телефоне не подключается:\n\n"
        "1. Выключи и снова включи VPN\n"
        "2. Проверь интернет без VPN\n"
        "3. Перезапусти приложение\n"
        "4. Переимпортируй ссылку\n"
        "5. Если не помогло — напиши в поддержку",
        reply_markup=get_support_faq_phone_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_phone_sites")
async def faq_phone_sites(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Если VPN на телефоне подключается, но интернет не работает:\n\n"
        "1. Переключи VPN заново\n"
        "2. Проверь доступ без VPN\n"
        "3. Перезапусти приложение\n"
        "4. Если проблема сохраняется — напиши в поддержку",
        reply_markup=get_support_faq_phone_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_phone_import")
async def faq_phone_import(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Если ссылка не импортируется на телефоне:\n\n"
        "1. Убедись, что копируешь ссылку полностью\n"
        "2. Проверь, в то ли приложение вставляешь ключ\n"
        "3. Попробуй скопировать ссылку заново\n"
        "4. Если не помогло — напиши в поддержку",
        reply_markup=get_support_faq_phone_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_phone_speed")
async def faq_phone_speed(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Если на телефоне низкая скорость:\n\n"
        "1. Проверь скорость без VPN\n"
        "2. Перезапусти VPN\n"
        "3. Переключись между Wi-Fi и мобильной сетью\n"
        "4. Если не помогло — напиши в поддержку",
        reply_markup=get_support_faq_phone_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_common_maintenance")
async def faq_common_maintenance(callback: CallbackQuery) -> None:
    status = get_server_status()
    await safe_edit(
        callback,
        "Информация о техработах:\n\n"
        f"Текущий статус: {status['status_code']}\n"
        f"{status['status_text']}",
        reply_markup=get_support_faq_common_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_common_renew")
async def faq_common_renew(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Как продлить подписку:\n\n"
        "1. Нажми «Продлить подписку» в главном меню\n"
        "2. Выбери срок\n"
        "3. Дождись обработки заявки\n\n"
        "Если активной подписки нет, сначала нужно получить ключ.",
        reply_markup=get_support_faq_common_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_faq_common_key")
async def faq_common_key(callback: CallbackQuery) -> None:
    await safe_edit(
        callback,
        "Если текущий ключ не работает:\n\n"
        "1. Проверь, не закончилась ли подписка\n"
        "2. Попробуй заново импортировать ключ\n"
        "3. Перезапусти приложение VPN\n"
        "4. Если не помогло — напиши в поддержку",
        reply_markup=get_support_faq_common_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_my_tickets")
async def support_my_tickets(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    await state.clear()
    tickets = get_user_tickets(callback.from_user.id)

    if not tickets:
        await safe_edit(
            callback,
            "У тебя пока нет обращений.",
            reply_markup=get_support_main_menu()
        )
        await callback.answer()
        return

    lines = ["Твои обращения:\n"]
    for ticket in tickets:
        topic = ticket["topic"] or "Без темы"
        lines.append(
            f"#{ticket['id']} | {topic} | {ticket['status']} | {ticket['created_at']}"
        )

    await safe_edit(
        callback,
        "\n".join(lines),
        reply_markup=get_support_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_create")
async def support_create(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    warning_text = get_status_warning_text()
    if warning_text:
        await safe_edit(
            callback,
            warning_text,
            reply_markup=get_support_warning_menu()
        )
        await callback.answer()
        return

    await state.set_state(UserSupportStates.choosing_topic)
    await safe_edit(
        callback,
        "Выбери тему обращения:",
        reply_markup=get_support_topic_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_continue_create")
async def support_continue_create(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(UserSupportStates.choosing_topic)
    await safe_edit(
        callback,
        "Выбери тему обращения:",
        reply_markup=get_support_topic_menu()
    )
    await callback.answer()


@router.callback_query(UserSupportStates.choosing_topic, F.data.startswith("support_topic_"))
async def support_choose_topic(callback: CallbackQuery, state: FSMContext) -> None:
    topic_code = callback.data.replace("support_topic_", "")
    topic_text = get_topic_text(topic_code)

    await state.update_data(topic_code=topic_code, topic_text=topic_text)
    await state.set_state(UserSupportStates.entering_message)

    await callback.message.answer(
        f"Тема: {topic_text}\n\n"
        "Теперь напиши сообщение в поддержку.\n\n"
        "Для отмены нажми кнопку ниже или напиши /cancel",
        reply_markup=get_support_cancel_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "support_cancel")
async def support_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "Создание обращения отменено.",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.message(UserSupportStates.entering_message)
async def process_support_message(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.from_user is None:
        await state.clear()
        return

    text = (message.text or "").strip()

    if not text:
        await message.answer("Сообщение не должно быть пустым.")
        return

    if len(text) > 2000:
        await message.answer("Сообщение слишком длинное.")
        return

    data = await state.get_data()
    topic_text = data.get("topic_text", "Другое")

    ticket_id = create_ticket(message.from_user.id, topic_text, text)

    config = load_config()
    username = f"@{message.from_user.username}" if message.from_user.username else "без username"

    admin_text = (
        f"Новое обращение #{ticket_id}\n\n"
        f"Тема: {topic_text}\n"
        f"Пользователь: {message.from_user.full_name}\n"
        f"Username: {username}\n"
        f"Telegram ID: {message.from_user.id}\n"
        f"Сообщение:\n{text}\n\n"
        "Команда для просмотра обращений: /tickets"
    )

    for admin_id in config.tg_bot.admins:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception:
            pass

    await state.clear()
    await message.answer(
        f"Обращение отправлено. Номер: #{ticket_id}",
        reply_markup=get_main_menu()
    )


@router.message(F.text == "/cancel")
async def cancel_user_support(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state not in (
        UserSupportStates.entering_message.state,
        UserSupportStates.choosing_topic.state,
    ):
        return

    await state.clear()
    await message.answer(
        "Создание обращения отменено.",
        reply_markup=get_main_menu()
    )