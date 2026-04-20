from aiogram import F, Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import logging

logger = logging.getLogger(__name__)

from bot.config import load_config
from bot.database.requests import (
    get_new_key_requests,
    get_renewal_requests,
    get_request_by_id,
    mark_trial_as_used,
    update_request_status,
)
from bot.database.subscriptions import (
    create_subscription_from_request,
    extend_active_subscription,
)
from bot.keyboards.admin_requests import get_admin_request_actions
from bot.states.admin_requests import (
    AdminIssueRequestStates,
    AdminRejectRequestStates,
)


router = Router(name=__name__)


def is_admin(telegram_id: int) -> bool:
    config = load_config()
    return telegram_id in config.tg_bot.admins


def format_request_card(request_data: dict) -> str:
    username = request_data["username"]
    username_text = f"@{username}" if username else "без username"
    full_name = request_data["full_name"] or request_data["first_name"] or "Без имени"

    if request_data["plan_type"] == "trial":
        plan_text = "Тест 3 дня"
    elif request_data["plan_type"] == "month":
        plan_text = "1 месяц"
    else:
        plan_text = f"{request_data['days_count']} дн."

    comment = request_data["comment"] or "Без комментария"
    request_type_text = "Новый ключ" if request_data["request_type"] == "new_key" else "Продление"

    return (
        f"Заявка #{request_data['id']}\n\n"
        f"Тип: {request_type_text}\n"
        f"Пользователь: {full_name}\n"
        f"Username: {username_text}\n"
        f"Telegram ID: {request_data['telegram_id']}\n"
        f"Срок: {plan_text}\n"
        f"Сумма: {request_data['amount_rub']} ₽\n"
        f"Статус оплаты: {request_data['payment_status']}\n"
        f"Комментарий: {comment}\n"
        f"Статус заявки: {request_data['status']}\n"
        f"Создана: {request_data['created_at']}"
    )


async def safe_edit_request(callback: CallbackQuery, text: str, request_id: int, status: str) -> None:
    try:
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_request_actions(request_id, status)
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.message(Command("requests"))
async def show_requests(message: Message, bot: Bot) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        return

    requests_list = get_new_key_requests() + get_renewal_requests()

    if not requests_list:
        await message.answer("Активных заявок нет.")
        return

    await message.answer(f"Найдено заявок: {len(requests_list)}")

    for request_data in requests_list:
        await message.answer(
            format_request_card(request_data),
            reply_markup=get_admin_request_actions(
                request_id=request_data["id"],
                status=request_data["status"]
            )
        )

        if request_data["payment_proof_file_id"]:
            try:
                if request_data["payment_proof_type"] == "photo":
                    await bot.send_photo(
                        message.chat.id,
                        request_data["payment_proof_file_id"],
                        caption=f"Подтверждение оплаты по заявке #{request_data['id']}"
                    )
                elif request_data["payment_proof_type"] == "document":
                    await bot.send_document(
                        message.chat.id,
                        request_data["payment_proof_file_id"],
                        caption=f"Подтверждение оплаты по заявке #{request_data['id']}"
                    )
            except Exception:
                pass


@router.callback_query(F.data.startswith("admin_req_take_"))
async def take_request(callback: CallbackQuery, bot: Bot) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    request_id = int(callback.data.rsplit("_", 1)[-1])
    request_data = get_request_by_id(request_id)

    if request_data is None:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    if request_data["status"] not in ("new", "in_progress"):
        await callback.answer("Эту заявку уже нельзя взять в работу.", show_alert=True)
        return

    update_request_status(request_id, "in_progress")
    updated = get_request_by_id(request_id)

    send_error = None
    try:
        await bot.send_message(
            chat_id=updated["telegram_id"],
            text=f"Твоя заявка #{updated['id']} принята в работу."
        )
    except Exception as e:
        send_error = str(e)

    await safe_edit_request(
        callback,
        format_request_card(updated),
        request_id=updated["id"],
        status=updated["status"]
    )

    if send_error:
        await callback.message.answer(
            "Статус заявки изменен, но уведомление пользователю не отправилось.\n"
            f"Ошибка: {send_error}\n"
            f"Telegram ID пользователя: {updated['telegram_id']}"
        )
    else:
        await callback.message.answer(
            f"Пользователю отправлено уведомление по заявке #{updated['id']}."
        )

    await callback.answer("Заявка взята в работу")


@router.callback_query(F.data.startswith("admin_req_issue_"))
async def start_issue_request(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    request_id = int(callback.data.rsplit("_", 1)[-1])
    request_data = get_request_by_id(request_id)

    if request_data is None:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    if request_data["status"] not in ("new", "in_progress"):
        await callback.answer("Эту заявку уже нельзя выдать.", show_alert=True)
        return

    await state.clear()
    await state.set_state(AdminIssueRequestStates.entering_access_text)
    await state.update_data(request_id=request_id)

    if request_data["request_type"] == "renewal":
        prompt = (
            f"Введи текст, который нужно отправить пользователю по заявке на продление #{request_id}.\n\n"
            "Это может быть подтверждение продления, инструкция или обновленный доступ.\n\n"
            "Для отмены напиши /cancel"
        )
    else:
        prompt = (
            f"Введи текст, который нужно отправить пользователю по заявке #{request_id}.\n\n"
            "Это может быть ключ, ссылка, инструкция или любое сообщение.\n\n"
            "Для отмены напиши /cancel"
        )

    await callback.message.answer(prompt)
    await callback.answer()


@router.message(AdminIssueRequestStates.entering_access_text)
async def process_issue_request(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await message.answer("Доступ запрещен.")
        await state.clear()
        return

    access_text = (message.text or "").strip()

    if not access_text:
        await message.answer("Текст не должен быть пустым.")
        return

    if len(access_text) > 3500:
        await message.answer("Слишком длинный текст. Уменьши сообщение.")
        return

    data = await state.get_data()
    request_id = data.get("request_id")

    if not request_id:
        await message.answer("Не удалось определить заявку.")
        await state.clear()
        return

    request_data = get_request_by_id(request_id)
    if request_data is None:
        await message.answer("Заявка не найдена.")
        await state.clear()
        return

    if request_data["status"] not in ("new", "in_progress"):
        await message.answer("Эта заявка уже неактуальна для выдачи.")
        await state.clear()
        return

    user_telegram_id = request_data["telegram_id"]

    if request_data["request_type"] == "renewal":
        user_message = (
            "Твоя подписка продлена.\n\n"
            f"{access_text}"
        )

        try:
            await bot.send_message(user_telegram_id, user_message)
        except Exception as e:
            await message.answer(
                "Не удалось отправить сообщение пользователю.\n"
                f"Ошибка: {e}"
            )
            return

        try:
            extend_active_subscription(
                telegram_id=user_telegram_id,
                days_count=request_data["days_count"],
                access_text=access_text,
            )
        except Exception as e:
            logger.exception("Ошибка при продлении подписки")

            await message.answer(
                "Не удалось продлить подписку.\n"
                f"Ошибка: {e}"
            )
            return

        update_request_status(request_id, "issued")
        await message.answer(f"Заявка на продление #{request_id} успешно обработана.")
        await state.clear()
        return

    user_message = (
        "Твоя заявка обработана.\n\n"
        f"{access_text}"
    )

    try:
        await bot.send_message(user_telegram_id, user_message)
    except Exception as e:
        await message.answer(
            "Не удалось отправить сообщение пользователю.\n"
            f"Ошибка: {e}"
        )
        return

    if request_data["plan_type"] == "trial":
        mark_trial_as_used(user_telegram_id)

    try:
        create_subscription_from_request(
            telegram_id=user_telegram_id,
            request_id=request_id,
            plan_type=request_data["plan_type"],
            days_count=request_data["days_count"],
            access_text=access_text,
        )
    except Exception as e:
        logger.exception("Ошибка при создании подписки")

        await message.answer(
            "Не удалось создать подписку в базе.\n"
            f"Ошибка: {e}"
        )
        await state.clear()
        return

    update_request_status(request_id, "issued")

    await message.answer(
        f"Заявка #{request_id} успешно выдана.\n"
        "Подписка создана."
    )

    await state.clear()


@router.callback_query(F.data.startswith("admin_req_reject_"))
async def start_reject_request(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен.", show_alert=True)
        return

    request_id = int(callback.data.rsplit("_", 1)[-1])
    request_data = get_request_by_id(request_id)

    if request_data is None:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    if request_data["status"] not in ("new", "in_progress"):
        await callback.answer("Эту заявку уже нельзя отклонить.", show_alert=True)
        return

    await state.clear()
    await state.set_state(AdminRejectRequestStates.entering_reject_reason)
    await state.update_data(request_id=request_id)

    await callback.message.answer(
        f"Введи причину отказа для заявки #{request_id}.\n\n"
        "Для отмены напиши /cancel"
    )
    await callback.answer()


@router.message(AdminRejectRequestStates.entering_reject_reason)
async def process_reject_request(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.from_user is None or not is_admin(message.from_user.id):
        await state.clear()
        return

    reject_reason = (message.text or "").strip()

    if not reject_reason:
        await message.answer("Причина отказа не должна быть пустой.")
        return

    if len(reject_reason) > 1000:
        await message.answer("Причина отказа слишком длинная.")
        return

    data = await state.get_data()
    request_id = data.get("request_id")

    if not request_id:
        await message.answer("Не удалось определить заявку.")
        await state.clear()
        return

    request_data = get_request_by_id(request_id)
    if request_data is None:
        await message.answer("Заявка не найдена.")
        await state.clear()
        return

    if request_data["status"] not in ("new", "in_progress"):
        await message.answer("Эта заявка уже неактуальна для отклонения.")
        await state.clear()
        return

    update_request_status(request_id, "rejected")

    send_error = None
    try:
        await bot.send_message(
            chat_id=request_data["telegram_id"],
            text=(
                f"Твоя заявка #{request_id} отклонена.\n\n"
                f"Причина: {reject_reason}"
            )
        )
    except Exception as e:
        send_error = str(e)

    if send_error:
        await message.answer(
            f"Заявка #{request_id} отклонена, но уведомление пользователю не отправилось.\n"
            f"Ошибка: {send_error}\n"
            f"Telegram ID пользователя: {request_data['telegram_id']}"
        )
    else:
        await message.answer(
            f"Заявка #{request_id} отклонена, уведомление пользователю отправлено."
        )

    await state.clear()


@router.message(Command("cancel"))
async def cancel_admin_action(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state is None:
        return

    await state.clear()
    await message.answer("Текущее действие отменено.")