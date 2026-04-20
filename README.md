# LenyaCloud Bots

Набор ботов для сервиса LenyaCloud:

- Telegram-бот — основной функционал (подписки, ключи, поддержка)
- VK-бот — резервный канал связи, если Telegram недоступен

## Возможности

### Telegram-бот
- Получение VPN-ключа
- Продление подписки
- Отправка заявок с подтверждением оплаты
- Система тикетов (поддержка)
- Уведомления пользователям
- Админ-панель внутри Telegram
- Управление статусом сервера
- Ссылка на резервный канал поддержки через VK

### VK-бот
- Резервный канал связи через VK
- Просмотр статуса сервера
- Создание обращения в поддержку
- Просмотр своих обращений
- Раздел "Частые проблемы"

## Технологии

- Python 3.10+
- aiogram 3
- vk_api
- SQLite

## Установка

1. Клонировать репозиторий:
```
git clone https://github.com/CoffEAM/LenyaCloud
cd LenyaCloud
```
2. Создать виртуальное окружение:
```
python -m venv .venv
source .venv/bin/activate # Linux/Mac
.venv\Scripts\activate # Windows
```
3. Установить зависимости:
```
pip install -r requirements.txt
```
4. Создать `.env` на основе `.env.example`
5. Запустить ботов:
```
python app.py
```

## Переменные окружения

- `BOT_TOKEN` — токен Telegram-бота
- `ADMINS` — список Telegram ID админов через запятую
- `CARD_NUMBER` — номер карты для оплаты
- `CARD_HOLDER` — имя получателя
- `VK_GROUP_TOKEN` — токен сообщества VK
- `VK_GROUP_ID` — ID сообщества VK
- `VK_GROUP_LINK` — ссылка на сообщество VK
- `BOT_DB_PATH` — путь к базе данных

## Структура проекта
```
bot/ # Telegram-бот
├── database/
├── handlers/
├── keyboards/
├── services/
├── states/
├── utils/
├── __init__.py
├── config.py
└── main.py

vk_bot/ # VK-бот
├── __init__.py
├── config.py
├── database.py
└── main.py

.env
app.py # общий запуск Telegram-бота и VK-бота
requirements.txt
```

## Безопасность

- `.env` не должен попадать в репозиторий
- база данных (`bot.db`) не хранится в GitHub
- токены и чувствительные данные не должны быть публичными
- админские действия защищены проверкой ID

## Лицензия

MIT