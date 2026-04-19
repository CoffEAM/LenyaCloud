# LenyaCloud VPN Bot

Telegram-бот для управления VPN-подписками и поддержкой пользователей.

## Возможности

- Получение VPN-ключа
- Продление подписки
- Отправка заявок с подтверждением оплаты
- Система тикетов (поддержка)
- Уведомления пользователям
- Админ-панель внутри Telegram
- Управление статусом сервера

## Технологии

- Python 3.10+
- aiogram 3
- SQLite

## Установка

1. Клонировать репозиторий:
```
git clone https://github.com/your_username/your_repo.git
cd your_repo
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
5. Запустить бота:
```
python bot/main.py
```
## Переменные окружения
- `BOT_TOKEN` — токен Telegram-бота
- `ADMINS` — список Telegram ID админов через запятую
- `CARD_NUMBER` — номер карты для оплаты
- `CARD_HOLDER` — имя получателя (опционально)
## Структура проекта
```
bot/
├── handlers/
├── keyboards/
├── database/
├── states/
├── services/
├── utils/
└── main.py
```
## Безопасность
- `.env` не должен попадать в репозиторий
- база данных (`bot.db`) не хранится в GitHub
- все админские действия защищены проверкой
## Лицензия
MIT