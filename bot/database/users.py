from aiogram.types import User

from bot.database.db import get_connection


def upsert_user(user: User, is_admin: bool = False) -> None:
    full_name = " ".join(
        part for part in [user.first_name, user.last_name] if part
    ).strip()

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
        INSERT INTO users (
            telegram_id,
            username,
            first_name,
            last_name,
            full_name,
            is_admin,
            last_seen_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name,
            last_name=excluded.last_name,
            full_name=excluded.full_name,
            is_admin=excluded.is_admin,
            last_seen_at=CURRENT_TIMESTAMP,
            updated_at=CURRENT_TIMESTAMP
        """, (
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            full_name,
            int(is_admin),
        ))

        connection.commit()


def get_user_by_telegram_id(telegram_id: int) -> dict | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

def get_all_active_users() -> list[dict]:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, telegram_id, username, first_name, last_name, full_name
            FROM users
            WHERE is_blocked = 0
            ORDER BY id ASC
        """)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]