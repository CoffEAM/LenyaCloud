from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_manual_subscription_type_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 месяц", callback_data="manual_sub_type_month")],
            [InlineKeyboardButton(text="Свой срок", callback_data="manual_sub_type_custom")],
            [InlineKeyboardButton(text="Бессрочная", callback_data="manual_sub_type_unlimited")],
            [InlineKeyboardButton(text="Отмена", callback_data="manual_sub_cancel")],
        ]
    )


def get_manual_subscription_confirm_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Подтвердить", callback_data="manual_sub_confirm"),
                InlineKeyboardButton(text="Отмена", callback_data="manual_sub_cancel"),
            ]
        ]
    )