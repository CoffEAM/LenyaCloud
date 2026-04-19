from bot.database.db import get_connection
from bot.database.requests import get_internal_user_id


def create_ticket(telegram_id: int, topic: str, text: str) -> int:
    user_id = get_internal_user_id(telegram_id)
    if user_id is None:
        raise ValueError("Пользователь не найден")

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO tickets (
                user_id,
                topic,
                status,
                updated_at
            )
            VALUES (?, ?, 'open', CURRENT_TIMESTAMP)
        """, (user_id, topic))
        ticket_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO ticket_messages (
                ticket_id,
                sender_type,
                text
            )
            VALUES (?, 'user', ?)
        """, (ticket_id, text))

        connection.commit()
        return int(ticket_id)


def get_open_tickets() -> list[dict]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                t.id,
                t.user_id,
                t.topic,
                t.status,
                t.created_at,
                t.updated_at,
                u.telegram_id,
                u.username,
                u.first_name,
                u.last_name,
                u.full_name
            FROM tickets t
            JOIN users u ON u.id = t.user_id
            WHERE t.status IN ('open', 'in_progress')
            ORDER BY t.created_at ASC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_user_tickets(telegram_id: int, limit: int = 10) -> list[dict]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                t.id,
                t.user_id,
                t.topic,
                t.status,
                t.created_at,
                t.updated_at
            FROM tickets t
            JOIN users u ON u.id = t.user_id
            WHERE u.telegram_id = ?
            ORDER BY t.id DESC
            LIMIT ?
        """, (telegram_id, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_ticket_by_id(ticket_id: int) -> dict | None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                t.id,
                t.user_id,
                t.topic,
                t.status,
                t.created_at,
                t.updated_at,
                u.telegram_id,
                u.username,
                u.first_name,
                u.last_name,
                u.full_name
            FROM tickets t
            JOIN users u ON u.id = t.user_id
            WHERE t.id = ?
        """, (ticket_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_ticket_last_message(ticket_id: int) -> dict | None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, ticket_id, sender_type, text, created_at
            FROM ticket_messages
            WHERE ticket_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (ticket_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def add_ticket_message(ticket_id: int, sender_type: str, text: str) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO ticket_messages (
                ticket_id,
                sender_type,
                text
            )
            VALUES (?, ?, ?)
        """, (ticket_id, sender_type, text))

        cursor.execute("""
            UPDATE tickets
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (ticket_id,))

        connection.commit()
        return int(cursor.lastrowid)


def update_ticket_status(ticket_id: int, status: str) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE tickets
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, ticket_id))
        connection.commit()