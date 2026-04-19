from aiogram import F, Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import load_config
from bot.database.requests import (
    create_new_key_request,
    create_renewal_request,
    has_active_new_key_request,
    has_active_renewal_request,
    has_used_trial,
)
from bot.database.subscriptions import (
    has_active_subscription,
    has_unlimited_active_subscription,
    mark_expired_subscriptions,
)
from bot.keyboards.request_key import (
    get_confirm_request_menu,
    get_key_plan_menu,
    get_payment_cancel_menu,
    get_renew_plan_menu,
    get_skip_comment_menu,
)
from bot.keyboards.user_menu import get_main_menu
from bot.services.pricing import calculate_price
from bot.states.requests import GetKeyStates, RenewSubscriptionStates


router = Router(name=__name__)


async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


def build_request_summary(
    plan_type: str,
    days_count: int,
    amount_rub: int,
    comment: str | None,
    title: str,
    payment_status: str,
) -> str:
    if plan_type == "trial":
        plan_text = "Тест 3 дня"
    elif plan_type == "month":
        plan_text = "1 месяц"
    else:
        plan_text = f"Свой срок: {days_count} дн."

    comment_text = comment if comment else "Без комментария"

    if payment_status == "not_required":
        payment_text = "Оплата не требуется"
    else:
        payment_text = f"{amount_rub} ₽, подтверждение приложено"

    return (
        f"{title}\n\n"
        f"Срок: {plan_text}\n"
        f"Оплата: {payment_text}\n"
        f"Комментарий: {comment_text}\n\n"
        "Подтвердить отправку?"
    )


def build_payment_text(plan_type: str, days_count: int, amount_rub: int) -> str:
    config = load_config()

    if plan_type == "month":
        plan_text = "1 месяц"
    else:
        plan_text = f"{days_count} дн."

    holder_text = f"\nПолучатель: {config.payment.card_holder}" if config.payment.card_holder else ""

    return (
        "Оплата заявки\n\n"
        f"Срок: {plan_text}\n"
        f"К оплате: {amount_rub} ₽\n"
        f"Карта: {config.payment.card_number}"
        f"{holder_text}\n\n"
        "После перевода пришли скриншот или фото подтверждения оплаты."
    )


def extract_payment_proof(message: Message) -> tuple[str | None, str | None]:
    if message.photo:
        return message.photo[-1].file_id, "photo"

    if message.document:
        return message.document.file_id, "document"

    return None, None


async def notify_admins_about_request(
    bot: Bot,
    request_id: int,
    request_type: str,
    full_name: str,
    username: str | None,
    telegram_id: int,
    plan_type: str,
    days_count: int,
    amount_rub: int,
    comment: str | None,
    payment_status: str,
    payment_proof_file_id: str | None,
    payment_proof_type: str | None,
) -> None:
    config = load_config()

    username_text = f"@{username}" if username else "без username"

    if plan_type == "trial":
        plan_text = "Тест 3 дня"
    elif plan_type == "month":
        plan_text = "1 месяц"
    else:
        plan_text = f"{days_count} дн."

    request_type_text = "новый ключ" if request_type == "new_key" else "продление"
    comment_text = comment if comment else "Без комментария"

    admin_text = (
        f"Новая заявка #{request_id}\n\n"
        f"Тип: {request_type_text}\n"
        f"Пользователь: {full_name}\n"
        f"Username: {username_text}\n"
        f"Telegram ID: {telegram_id}\n"
        f"Срок: {plan_text}\n"
        f"Сумма: {amount_rub} ₽\n"
        f"Статус оплаты: {payment_status}\n"
        f"Комментарий: {comment_text}\n\n"
        "Для просмотра заявок используй /requests"
    )

    for admin_id in config.tg_bot.admins:
        try:
            await bot.send_message(admin_id, admin_text)

            if payment_proof_file_id and payment_proof_type == "photo":
                await bot.send_photo(
                    admin_id,
                    payment_proof_file_id,
                    caption=f"Подтверждение оплаты по заявке #{request_id}"
                )
            elif payment_proof_file_id and payment_proof_type == "document":
                await bot.send_document(
                    admin_id,
                    payment_proof_file_id,
                    caption=f"Подтверждение оплаты по заявке #{request_id}"
                )
        except Exception:
            pass


@router.callback_query(F.data == "menu_get_key")
async def start_get_key(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    mark_expired_subscriptions()

    if has_active_subscription(callback.from_user.id):
        await safe_edit(
            callback,
            "У тебя уже есть активная подписка.\n\n"
            "Если нужен новый доступ или замена ключа, напиши в поддержку.",
            reply_markup=get_main_menu()
        )
        await state.clear()
        await callback.answer()
        return

    if has_active_new_key_request(callback.from_user.id):
        await safe_edit(
            callback,
            "У тебя уже есть активная заявка на получение ключа.\n"
            "Дождись обработки или напиши в поддержку.",
            reply_markup=get_main_menu()
        )
        await state.clear()
        await callback.answer()
        return

    trial_available = not has_used_trial(callback.from_user.id)

    await state.clear()
    await state.set_state(GetKeyStates.choosing_plan)

    await safe_edit(
        callback,
        "Выбери вариант получения ключа:",
        reply_markup=get_key_plan_menu(show_trial=trial_available)
    )
    await callback.answer()


@router.callback_query(F.data == "menu_renew")
async def start_renew_subscription(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    mark_expired_subscriptions()

    if not has_active_subscription(callback.from_user.id):
        await safe_edit(
            callback,
            "Активной подписки нет.\n\n"
            "Сначала нужно получить ключ.",
            reply_markup=get_main_menu()
        )
        await state.clear()
        await callback.answer()
        return

    if has_unlimited_active_subscription(callback.from_user.id):
        await safe_edit(
            callback,
            "У тебя бессрочная подписка.\n\n"
            "Продление не требуется.",
            reply_markup=get_main_menu()
        )
        await state.clear()
        await callback.answer()
        return

    if has_active_renewal_request(callback.from_user.id):
        await safe_edit(
            callback,
            "У тебя уже есть активная заявка на продление.\n"
            "Дождись обработки или напиши в поддержку.",
            reply_markup=get_main_menu()
        )
        await state.clear()
        await callback.answer()
        return

    await state.clear()
    await state.set_state(RenewSubscriptionStates.choosing_plan)

    await safe_edit(
        callback,
        "Выбери срок продления:",
        reply_markup=get_renew_plan_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "get_key_back_main")
@router.callback_query(F.data == "renew_back_main")
async def any_back_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(
        callback,
        "Главное меню:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@router.callback_query(GetKeyStates.choosing_plan, F.data == "get_key_plan_trial")
async def choose_trial(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    if has_used_trial(callback.from_user.id):
        await callback.answer("Тестовый доступ уже был использован.", show_alert=True)
        return

    await state.update_data(plan_type="trial", days_count=3, amount_rub=0)
    await state.set_state(GetKeyStates.entering_comment)

    await safe_edit(
        callback,
        "Ты выбрал: Тест 3 дня.\n\n"
        "Теперь напиши комментарий к заявке или нажми «Пропустить».",
        reply_markup=get_skip_comment_menu(prefix="get_key")
    )
    await callback.answer()


@router.callback_query(GetKeyStates.choosing_plan, F.data == "get_key_plan_month")
async def choose_month(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(plan_type="month", days_count=30, amount_rub=100)
    await state.set_state(GetKeyStates.entering_comment)

    await safe_edit(
        callback,
        "Ты выбрал: 1 месяц.\n\n"
        "Теперь напиши комментарий к заявке или нажми «Пропустить».",
        reply_markup=get_skip_comment_menu(prefix="get_key")
    )
    await callback.answer()


@router.callback_query(GetKeyStates.choosing_plan, F.data == "get_key_plan_custom")
async def choose_custom(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GetKeyStates.entering_custom_days)

    await safe_edit(
        callback,
        "Введи срок в днях.\nНапример: 7, 14, 30",
        reply_markup=None
    )
    await callback.answer()


@router.message(GetKeyStates.entering_custom_days)
async def process_custom_days(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()

    if not text.isdigit():
        await message.answer("Нужно ввести целое число дней. Например: 7")
        return

    days_count = int(text)

    if days_count < 1:
        await message.answer("Срок должен быть больше 0.")
        return

    if days_count > 3650:
        await message.answer("Слишком большой срок. Введи число до 3650 дней.")
        return

    amount_rub = calculate_price("custom", days_count)

    await state.update_data(plan_type="custom", days_count=days_count, amount_rub=amount_rub)
    await state.set_state(GetKeyStates.entering_comment)

    await message.answer(
        f"Срок {days_count} дн. сохранен.\n"
        f"Сумма к оплате: {amount_rub} ₽\n\n"
        "Теперь напиши комментарий к заявке или нажми «Пропустить».",
        reply_markup=get_skip_comment_menu(prefix="get_key")
    )


@router.callback_query(GetKeyStates.entering_comment, F.data == "get_key_skip_comment")
async def skip_comment_get_key(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    plan_type = data["plan_type"]
    days_count = data["days_count"]
    amount_rub = data["amount_rub"]

    await state.update_data(comment=None)

    if amount_rub == 0:
        await state.update_data(
            payment_status="not_required",
            payment_proof_file_id=None,
            payment_proof_type=None,
        )
        await state.set_state(GetKeyStates.confirming_request)

        await safe_edit(
            callback,
            build_request_summary(
                plan_type,
                days_count,
                amount_rub,
                None,
                "Проверь заявку на получение ключа:",
                "not_required"
            ),
            reply_markup=get_confirm_request_menu(prefix="get_key")
        )
    else:
        await state.set_state(GetKeyStates.waiting_payment_proof)
        await safe_edit(
            callback,
            build_payment_text(plan_type, days_count, amount_rub),
            reply_markup=get_payment_cancel_menu(prefix="get_key")
        )

    await callback.answer()


@router.message(GetKeyStates.entering_comment)
async def process_comment_get_key(message: Message, state: FSMContext) -> None:
    comment = (message.text or "").strip()

    if len(comment) > 1000:
        await message.answer("Комментарий слишком длинный. Максимум 1000 символов.")
        return

    data = await state.get_data()
    amount_rub = data["amount_rub"]
    plan_type = data["plan_type"]
    days_count = data["days_count"]

    await state.update_data(comment=comment)

    if amount_rub == 0:
        await state.update_data(
            payment_status="not_required",
            payment_proof_file_id=None,
            payment_proof_type=None,
        )
        await state.set_state(GetKeyStates.confirming_request)

        await message.answer(
            build_request_summary(
                plan_type,
                days_count,
                amount_rub,
                comment,
                "Проверь заявку на получение ключа:",
                "not_required"
            ),
            reply_markup=get_confirm_request_menu(prefix="get_key")
        )
    else:
        await state.set_state(GetKeyStates.waiting_payment_proof)
        await message.answer(
            build_payment_text(plan_type, days_count, amount_rub),
            reply_markup=get_payment_cancel_menu(prefix="get_key")
        )


@router.message(GetKeyStates.waiting_payment_proof, F.photo | F.document)
async def process_get_key_payment_proof(message: Message, state: FSMContext) -> None:
    file_id, proof_type = extract_payment_proof(message)

    if not file_id or not proof_type:
        await message.answer("Пришли скриншот или документ с подтверждением оплаты.")
        return

    data = await state.get_data()
    plan_type = data["plan_type"]
    days_count = data["days_count"]
    amount_rub = data["amount_rub"]
    comment = data.get("comment")

    await state.update_data(
        payment_status="proof_sent",
        payment_proof_file_id=file_id,
        payment_proof_type=proof_type,
    )
    await state.set_state(GetKeyStates.confirming_request)

    await message.answer(
        build_request_summary(
            plan_type,
            days_count,
            amount_rub,
            comment,
            "Проверь заявку на получение ключа:",
            "proof_sent"
        ),
        reply_markup=get_confirm_request_menu(prefix="get_key")
    )


@router.message(GetKeyStates.waiting_payment_proof)
async def process_get_key_wrong_payment_proof(message: Message) -> None:
    await message.answer("Нужно отправить скриншот оплаты как фото или документ.")


@router.callback_query(GetKeyStates.confirming_request, F.data == "get_key_confirm")
async def confirm_request(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    if has_active_new_key_request(callback.from_user.id):
        await safe_edit(
            callback,
            "У тебя уже есть активная заявка на получение ключа.\n"
            "Новая заявка не создана.",
            reply_markup=get_main_menu()
        )
        await state.clear()
        await callback.answer()
        return

    data = await state.get_data()

    request_id = create_new_key_request(
        telegram_id=callback.from_user.id,
        plan_type=data["plan_type"],
        days_count=data["days_count"],
        amount_rub=data["amount_rub"],
        payment_status=data["payment_status"],
        payment_proof_file_id=data.get("payment_proof_file_id"),
        payment_proof_type=data.get("payment_proof_type"),
        comment=data.get("comment"),
    )

    await notify_admins_about_request(
        bot=bot,
        request_id=request_id,
        request_type="new_key",
        full_name=callback.from_user.full_name,
        username=callback.from_user.username,
        telegram_id=callback.from_user.id,
        plan_type=data["plan_type"],
        days_count=data["days_count"],
        amount_rub=data["amount_rub"],
        comment=data.get("comment"),
        payment_status=data["payment_status"],
        payment_proof_file_id=data.get("payment_proof_file_id"),
        payment_proof_type=data.get("payment_proof_type"),
    )

    await state.clear()

    await safe_edit(
        callback,
        "Заявка отправлена.\n\n"
        f"Номер заявки: {request_id}",
        reply_markup=get_main_menu()
    )
    await callback.answer("Заявка создана")


@router.callback_query(RenewSubscriptionStates.choosing_plan, F.data == "renew_plan_month")
async def choose_renew_month(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(plan_type="month", days_count=30, amount_rub=100)
    await state.set_state(RenewSubscriptionStates.entering_comment)

    await safe_edit(
        callback,
        "Ты выбрал продление на 1 месяц.\n\n"
        "Теперь напиши комментарий к заявке или нажми «Пропустить».",
        reply_markup=get_skip_comment_menu(prefix="renew")
    )
    await callback.answer()


@router.callback_query(RenewSubscriptionStates.choosing_plan, F.data == "renew_plan_custom")
async def choose_renew_custom(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(RenewSubscriptionStates.entering_custom_days)

    await safe_edit(
        callback,
        "Введи срок продления в днях.\nНапример: 7, 14, 30",
        reply_markup=None
    )
    await callback.answer()


@router.message(RenewSubscriptionStates.entering_custom_days)
async def process_renew_custom_days(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()

    if not text.isdigit():
        await message.answer("Нужно ввести целое число дней. Например: 7")
        return

    days_count = int(text)

    if days_count < 1:
        await message.answer("Срок должен быть больше 0.")
        return

    if days_count > 3650:
        await message.answer("Слишком большой срок. Введи число до 3650 дней.")
        return

    amount_rub = calculate_price("custom", days_count)

    await state.update_data(plan_type="custom", days_count=days_count, amount_rub=amount_rub)
    await state.set_state(RenewSubscriptionStates.entering_comment)

    await message.answer(
        f"Продление на {days_count} дн. сохранено.\n"
        f"Сумма к оплате: {amount_rub} ₽\n\n"
        "Теперь напиши комментарий к заявке или нажми «Пропустить».",
        reply_markup=get_skip_comment_menu(prefix="renew")
    )


@router.callback_query(RenewSubscriptionStates.entering_comment, F.data == "renew_skip_comment")
async def skip_comment_renew(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    plan_type = data["plan_type"]
    days_count = data["days_count"]
    amount_rub = data["amount_rub"]

    await state.update_data(comment=None)
    await state.set_state(RenewSubscriptionStates.waiting_payment_proof)

    await safe_edit(
        callback,
        build_payment_text(plan_type, days_count, amount_rub),
        reply_markup=get_payment_cancel_menu(prefix="renew")
    )
    await callback.answer()


@router.message(RenewSubscriptionStates.entering_comment)
async def process_comment_renew(message: Message, state: FSMContext) -> None:
    comment = (message.text or "").strip()

    if len(comment) > 1000:
        await message.answer("Комментарий слишком длинный. Максимум 1000 символов.")
        return

    data = await state.get_data()
    amount_rub = data["amount_rub"]
    plan_type = data["plan_type"]
    days_count = data["days_count"]

    await state.update_data(comment=comment)
    await state.set_state(RenewSubscriptionStates.waiting_payment_proof)

    await message.answer(
        build_payment_text(plan_type, days_count, amount_rub),
        reply_markup=get_payment_cancel_menu(prefix="renew")
    )


@router.message(RenewSubscriptionStates.waiting_payment_proof, F.photo | F.document)
async def process_renew_payment_proof(message: Message, state: FSMContext) -> None:
    file_id, proof_type = extract_payment_proof(message)

    if not file_id or not proof_type:
        await message.answer("Пришли скриншот или документ с подтверждением оплаты.")
        return

    data = await state.get_data()
    plan_type = data["plan_type"]
    days_count = data["days_count"]
    amount_rub = data["amount_rub"]
    comment = data.get("comment")

    await state.update_data(
        payment_status="proof_sent",
        payment_proof_file_id=file_id,
        payment_proof_type=proof_type,
    )
    await state.set_state(RenewSubscriptionStates.confirming_request)

    await message.answer(
        build_request_summary(
            plan_type,
            days_count,
            amount_rub,
            comment,
            "Проверь заявку на продление:",
            "proof_sent"
        ),
        reply_markup=get_confirm_request_menu(prefix="renew")
    )


@router.message(RenewSubscriptionStates.waiting_payment_proof)
async def process_renew_wrong_payment_proof(message: Message) -> None:
    await message.answer("Нужно отправить скриншот оплаты как фото или документ.")


@router.callback_query(RenewSubscriptionStates.confirming_request, F.data == "renew_confirm")
async def confirm_renew_request(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if callback.from_user is None:
        await callback.answer()
        return

    if has_active_renewal_request(callback.from_user.id):
        await safe_edit(
            callback,
            "У тебя уже есть активная заявка на продление.\n"
            "Новая заявка не создана.",
            reply_markup=get_main_menu()
        )
        await state.clear()
        await callback.answer()
        return

    data = await state.get_data()

    request_id = create_renewal_request(
        telegram_id=callback.from_user.id,
        plan_type=data["plan_type"],
        days_count=data["days_count"],
        amount_rub=data["amount_rub"],
        payment_status=data["payment_status"],
        payment_proof_file_id=data.get("payment_proof_file_id"),
        payment_proof_type=data.get("payment_proof_type"),
        comment=data.get("comment"),
    )

    await notify_admins_about_request(
        bot=bot,
        request_id=request_id,
        request_type="renewal",
        full_name=callback.from_user.full_name,
        username=callback.from_user.username,
        telegram_id=callback.from_user.id,
        plan_type=data["plan_type"],
        days_count=data["days_count"],
        amount_rub=data["amount_rub"],
        comment=data.get("comment"),
        payment_status=data["payment_status"],
        payment_proof_file_id=data.get("payment_proof_file_id"),
        payment_proof_type=data.get("payment_proof_type"),
    )

    await state.clear()

    await safe_edit(
        callback,
        "Заявка на продление отправлена.\n\n"
        f"Номер заявки: {request_id}",
        reply_markup=get_main_menu()
    )
    await callback.answer("Заявка создана")


@router.callback_query(F.data == "get_key_cancel")
@router.callback_query(F.data == "renew_cancel")
async def cancel_request(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(
        callback,
        "Создание заявки отменено.",
        reply_markup=get_main_menu()
    )
    await callback.answer()