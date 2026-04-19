from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_key_plan_menu(show_trial: bool = True) -> InlineKeyboardMarkup:
    rows = []

    if show_trial:
        rows.append([InlineKeyboardButton(text="Тест 3 дня", callback_data="get_key_plan_trial")])

    rows.extend([
        [InlineKeyboardButton(text="1 месяц", callback_data="get_key_plan_month")],
        [InlineKeyboardButton(text="Свой срок", callback_data="get_key_plan_custom")],
        [InlineKeyboardButton(text="Назад", callback_data="get_key_back_main")],
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_renew_plan_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 месяц", callback_data="renew_plan_month")],
            [InlineKeyboardButton(text="Свой срок", callback_data="renew_plan_custom")],
            [InlineKeyboardButton(text="Назад", callback_data="renew_back_main")],
        ]
    )


def get_skip_comment_menu(prefix: str = "get_key") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data=f"{prefix}_skip_comment")]
        ]
    )


def get_payment_cancel_menu(prefix: str = "get_key") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data=f"{prefix}_cancel")]
        ]
    )


def get_confirm_request_menu(prefix: str = "get_key") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Подтвердить", callback_data=f"{prefix}_confirm"),
                InlineKeyboardButton(text="Отмена", callback_data=f"{prefix}_cancel"),
            ]
        ]
    )