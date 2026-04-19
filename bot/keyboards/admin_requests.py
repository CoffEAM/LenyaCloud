from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_request_actions(request_id: int, status: str) -> InlineKeyboardMarkup:
    rows = []

    if status == "new":
        rows.append([
            InlineKeyboardButton(
                text="Взять в работу",
                callback_data=f"admin_req_take_{request_id}"
            )
        ])

    if status in ("new", "in_progress"):
        rows.append([
            InlineKeyboardButton(
                text="Выдать",
                callback_data=f"admin_req_issue_{request_id}"
            ),
            InlineKeyboardButton(
                text="Отклонить",
                callback_data=f"admin_req_reject_{request_id}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=rows)