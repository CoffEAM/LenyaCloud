from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import logging

logger = logging.getLogger(__name__)

from bot.config import load_config
from bot.database.subscriptions import create_manual_subscription
from bot.keyboards.manual_subscription import (
    get_manual_subscription_confirm_menu,
    get_manual_subscription_type_menu,
)
from bot.states.manual_subscription import ManualSubscriptionStates


router = Router(name=__name__)


def is_admin(user_id: int) -> bool:
    return user_id in load_config().tg_bot.admins


def build_manual_subscription_summary(
    telegram_id: int,
    plan_type: str,
    days_count: int | None,
    access_text: str,
    is_unlimited: bool,
) -> str:
    if is_unlimited:
        plan_text = "Бессрочная"
    elif plan_type == "month":
        plan_text = "1 месяц"
    else:
        plan_text = f"Свой срок: {days_count} дн."

    return (
        "Проверь данные подписки:\n\n"
        f"Telegram ID: {telegram_id}\n"
        f"Тип: {plan_text}\n"
        f"Текст доступа: {access_text}\n\n"
        "Создать подписку?"
    )


@router.message(Command("addsub"))
async def start_add_sub(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        return

    await state.clear()
    await state.set_state(ManualSubscriptionStates.entering_user_id)
    await message.answer(
        "Введи Telegram ID пользователя, которому нужно добавить подписку.\n\n"
        "Для отмены напиши /cancel"
    )


@router.message(ManualSubscriptionStates.entering_user_id)
async def process_manual_sub_user_id(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await state.clear()
        return

    text = (message.text or "").strip()

    if not text.isdigit():
        await message.answer("Telegram ID должен быть числом.")
        return

    await state.update_data(telegram_id=int(text))
    await state.set_state(ManualSubscriptionStates.choosing_type)

    await message.answer(
        "Выбери тип подписки:",
        reply_markup=get_manual_subscription_type_menu()
    )


@router.callback_query(ManualSubscriptionStates.choosing_type, F.data == "manual_sub_type_month")
async def choose_manual_month(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(
        plan_type="month",
        days_count=30,
        is_unlimited=False
    )
    await state.set_state(ManualSubscriptionStates.entering_access_text)
    await callback.message.answer("Введи текст доступа или заметку для подписки.")
    await callback.answer()


@router.callback_query(ManualSubscriptionStates.choosing_type, F.data == "manual_sub_type_custom")
async def choose_manual_custom(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ManualSubscriptionStates.entering_days)
    await callback.message.answer("Введи срок в днях.")
    await callback.answer()


@router.callback_query(ManualSubscriptionStates.choosing_type, F.data == "manual_sub_type_unlimited")
async def choose_manual_unlimited(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(
        plan_type="unlimited",
        days_count=None,
        is_unlimited=True
    )
    await state.set_state(ManualSubscriptionStates.entering_access_text)
    await callback.message.answer("Введи текст доступа или заметку для подписки.")
    await callback.answer()


@router.message(ManualSubscriptionStates.entering_days)
async def process_manual_sub_days(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await state.clear()
        return

    text = (message.text or "").strip()

    if not text.isdigit():
        await message.answer("Нужно ввести число дней.")
        return

    days_count = int(text)

    if days_count < 1:
        await message.answer("Срок должен быть больше 0.")
        return

    if days_count > 3650:
        await message.answer("Слишком большой срок. Введи число до 3650.")
        return

    await state.update_data(
        plan_type="custom",
        days_count=days_count,
        is_unlimited=False
    )
    await state.set_state(ManualSubscriptionStates.entering_access_text)
    await message.answer("Теперь введи текст доступа или заметку для подписки.")


@router.message(ManualSubscriptionStates.entering_access_text)
async def process_manual_sub_access_text(message: Message, state: FSMContext) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await state.clear()
        return

    access_text = (message.text or "").strip()

    if not access_text:
        await message.answer("Текст не должен быть пустым.")
        return

    if len(access_text) > 3500:
        await message.answer("Слишком длинный текст.")
        return

    await state.update_data(access_text=access_text)

    data = await state.get_data()

    await state.set_state(ManualSubscriptionStates.entering_confirm)
    await message.answer(
        build_manual_subscription_summary(
            telegram_id=data["telegram_id"],
            plan_type=data["plan_type"],
            days_count=data.get("days_count"),
            access_text=access_text,
            is_unlimited=data["is_unlimited"],
        ),
        reply_markup=get_manual_subscription_confirm_menu()
    )


@router.callback_query(ManualSubscriptionStates.entering_confirm, F.data == "manual_sub_confirm")
async def confirm_manual_sub(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await state.clear()
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    data = await state.get_data()

    try:
        subscription_id = create_manual_subscription(
            telegram_id=data["telegram_id"],
            plan_type=data["plan_type"],
            days_count=data.get("days_count"),
            access_text=data["access_text"],
            is_unlimited=data["is_unlimited"],
        )
    except Exception as e:
        logger.exception("Ошибка при ручном создании подписки")

        await callback.message.answer(
            "Не удалось создать подписку вручную.\n"
            f"Ошибка: {e}"
        )
        await state.clear()
        return

    await state.clear()
    await callback.message.answer(f"Подписка создана. ID подписки: {subscription_id}")
    await callback.answer("Подписка добавлена")


@router.callback_query(F.data == "manual_sub_cancel")
async def cancel_manual_sub(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Добавление подписки отменено.")
    await callback.answer()