from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_support_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Частые проблемы", callback_data="support_faq")],
            [InlineKeyboardButton(text="Написать в поддержку", callback_data="support_create")],
            [InlineKeyboardButton(text="Мои обращения", callback_data="support_my_tickets")],
            [InlineKeyboardButton(text="Назад", callback_data="support_back_main")],
        ]
    )


def get_support_warning_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Все равно написать", callback_data="support_continue_create")],
            [InlineKeyboardButton(text="Частые проблемы", callback_data="support_faq")],
            [InlineKeyboardButton(text="Назад", callback_data="support_back_main")],
        ]
    )


def get_support_topic_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Проблема с VPN на ПК", callback_data="support_topic_pc")],
            [InlineKeyboardButton(text="Проблема с VPN на телефоне", callback_data="support_topic_phone")],
            [InlineKeyboardButton(text="Продление подписки", callback_data="support_topic_renew")],
            [InlineKeyboardButton(text="Новый ключ", callback_data="support_topic_key")],
            [InlineKeyboardButton(text="Другое", callback_data="support_topic_other")],
            [InlineKeyboardButton(text="Назад", callback_data="support_back_support")],
        ]
    )


def get_support_cancel_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="support_cancel")]
        ]
    )


def get_support_faq_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Проблемы на ПК", callback_data="support_faq_pc")],
            [InlineKeyboardButton(text="Проблемы на телефоне", callback_data="support_faq_phone")],
            [InlineKeyboardButton(text="Общие вопросы", callback_data="support_faq_common")],
            [InlineKeyboardButton(text="Назад", callback_data="support_back_support")],
        ]
    )


def get_support_faq_pc_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="VPN не подключается", callback_data="support_faq_pc_connect")],
            [InlineKeyboardButton(text="Подключается, но сайты не открываются", callback_data="support_faq_pc_sites")],
            [InlineKeyboardButton(text="Низкая скорость", callback_data="support_faq_pc_speed")],
            [InlineKeyboardButton(text="Не импортируется ключ", callback_data="support_faq_pc_import")],
            [InlineKeyboardButton(text="Назад", callback_data="support_faq")],
        ]
    )


def get_support_faq_phone_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="VPN не подключается", callback_data="support_faq_phone_connect")],
            [InlineKeyboardButton(text="Подключается, но интернет не работает", callback_data="support_faq_phone_sites")],
            [InlineKeyboardButton(text="Не импортируется ссылка", callback_data="support_faq_phone_import")],
            [InlineKeyboardButton(text="Низкая скорость", callback_data="support_faq_phone_speed")],
            [InlineKeyboardButton(text="Назад", callback_data="support_faq")],
        ]
    )


def get_support_faq_common_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Идут ли техработы", callback_data="support_faq_common_maintenance")],
            [InlineKeyboardButton(text="Как продлить подписку", callback_data="support_faq_common_renew")],
            [InlineKeyboardButton(text="Что делать, если ключ не работает", callback_data="support_faq_common_key")],
            [InlineKeyboardButton(text="Назад", callback_data="support_faq")],
        ]
    )


def get_admin_ticket_actions(ticket_id: int, status: str) -> InlineKeyboardMarkup:
    rows = []

    if status == "open":
        rows.append([
            InlineKeyboardButton(
                text="Взять в работу",
                callback_data=f"admin_ticket_take_{ticket_id}"
            )
        ])

    if status in ("open", "in_progress"):
        rows.append([
            InlineKeyboardButton(
                text="Ответить",
                callback_data=f"admin_ticket_reply_{ticket_id}"
            ),
            InlineKeyboardButton(
                text="Закрыть",
                callback_data=f"admin_ticket_close_{ticket_id}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)