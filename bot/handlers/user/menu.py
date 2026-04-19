from datetime import datetime

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from bot.database.subscriptions import (
    get_latest_subscription_by_telegram_id,
    mark_expired_subscriptions,
)
from bot.database.server_status import get_server_status
from bot.keyboards.user_menu import get_main_menu


router = Router(name=__name__)


async def safe_edit(callback: CallbackQuery, text: str) -> None:
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_main_menu()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.callback_query(F.data == "menu_subscription")
async def my_subscription_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    mark_expired_subscriptions()
    subscription = get_latest_subscription_by_telegram_id(callback.from_user.id)

    if subscription is None:
        await safe_edit(
            callback,
            "Подписка не найдена."
        )
        await callback.answer()
        return

    if subscription["is_unlimited"]:
        text = (
            "Текущая подписка:\n\n"
            "Тип: бессрочная\n"
            f"Дата начала: {subscription['starts_at']}\n"
            "Срок: ∞"
        )
    else:
        expires_at = datetime.strptime(subscription["expires_at"], "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        remaining = expires_at - now
        remaining_days = max(0, remaining.days)
        remaining_hours = max(0, remaining.seconds // 3600)

        plan_map = {
            "trial": "Тест 3 дня",
            "month": "1 месяц",
            "custom": f"{subscription['days_count']} дн.",
        }
        plan_text = plan_map.get(subscription["plan_type"], f"{subscription['days_count']} дн.")

        if subscription["status"] == "expired":
            text = (
                "Подписка найдена.\n\n"
                f"Тариф: {plan_text}\n"
                f"Статус: истекла\n"
                f"Дата окончания: {subscription['expires_at']}"
            )
        else:
            text = (
                "Текущая подписка:\n\n"
                f"Тариф: {plan_text}\n"
                f"Статус: активна\n"
                f"Дата начала: {subscription['starts_at']}\n"
                f"Дата окончания: {subscription['expires_at']}\n"
                f"Осталось: {remaining_days} дн. {remaining_hours} ч."
            )

    await safe_edit(callback, text)
    await callback.answer()


@router.callback_query(F.data == "menu_server_status")
async def server_status_handler(callback: CallbackQuery) -> None:
    status = get_server_status()

    if status["status_code"] == "ok":
        text = (
            "Статус сервера:\n\n"
            "Работает\n"
            f"{status['status_text']}"
        )
    elif status["status_code"] == "maintenance":
        text = (
            "Статус сервера:\n\n"
            "Технические работы\n"
            f"{status['status_text']}"
        )
    else:
        text = (
            "Статус сервера:\n\n"
            "Есть известные проблемы\n"
            f"{status['status_text']}"
        )

    await safe_edit(callback, text)
    await callback.answer()


@router.callback_query(F.data == "menu_instruction")
async def instruction_handler(callback: CallbackQuery) -> None:
    await safe_edit(callback, "Инструкция по подключению пока в разработке.")
    await callback.answer()