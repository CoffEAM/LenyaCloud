from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Получить ключ", callback_data="menu_get_key")],
            [
                InlineKeyboardButton(text="Продлить подписку", callback_data="menu_renew"),
                InlineKeyboardButton(text="Моя подписка", callback_data="menu_subscription"),
            ],
            [
                InlineKeyboardButton(text="Поддержка", callback_data="menu_support"),
                InlineKeyboardButton(text="Статус сервера", callback_data="menu_server_status"),
            ],
            [InlineKeyboardButton(text="Инструкция", callback_data="menu_instruction")],
        ]
    )