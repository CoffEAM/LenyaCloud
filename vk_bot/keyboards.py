from vkbottle import Keyboard, KeyboardButtonColor, Text


def get_main_keyboard() -> str:
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("Статус сервера"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("Поддержка"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("Частые проблемы"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("Мои обращения"), color=KeyboardButtonColor.SECONDARY)
    return keyboard.get_json()


def get_support_topic_keyboard() -> str:
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("VPN на ПК"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("VPN на телефоне"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("Продление подписки"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("Новый ключ"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("Другое"), color=KeyboardButtonColor.NEGATIVE)
    keyboard.row()
    keyboard.add(Text("Назад"), color=KeyboardButtonColor.SECONDARY)
    return keyboard.get_json()


def get_faq_keyboard() -> str:
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("Проблемы на ПК"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("Проблемы на телефоне"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("Общие вопросы"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("Назад"), color=KeyboardButtonColor.SECONDARY)
    return keyboard.get_json()