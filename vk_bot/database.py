import sqlite3
from pathlib import Path
from typing import Any


class VkDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_vk_tables(self) -> None:
        with self.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS vk_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vk_id INTEGER NOT NULL UNIQUE,
                full_name TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS vk_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES vk_users(id)
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS vk_ticket_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES vk_tickets(id)
            )
            """)

            connection.commit()

    def upsert_vk_user(self, vk_id: int, full_name: str) -> None:
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO vk_users (
                    vk_id,
                    full_name,
                    updated_at
                )
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(vk_id) DO UPDATE SET
                    full_name = excluded.full_name,
                    updated_at = CURRENT_TIMESTAMP
            """, (vk_id, full_name))
            connection.commit()

    def get_internal_vk_user_id(self, vk_id: int) -> int | None:
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id FROM vk_users WHERE vk_id = ?",
                (vk_id,)
            )
            row = cursor.fetchone()
            return int(row["id"]) if row else None

    def create_ticket(self, vk_id: int, full_name: str, topic: str, text: str) -> int:
        self.upsert_vk_user(vk_id, full_name)

        user_id = self.get_internal_vk_user_id(vk_id)
        if user_id is None:
            raise ValueError("Не удалось сохранить VK-пользователя")

        with self.get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO vk_tickets (
                    user_id,
                    topic,
                    status,
                    updated_at
                )
                VALUES (?, ?, 'open', CURRENT_TIMESTAMP)
            """, (user_id, topic))
            ticket_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO vk_ticket_messages (
                    ticket_id,
                    sender_type,
                    text
                )
                VALUES (?, 'user', ?)
            """, (ticket_id, text))

            connection.commit()
            return int(ticket_id)

    def get_user_tickets(self, vk_id: int, limit: int = 10) -> list[dict[str, Any]]:
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT
                    t.id,
                    t.topic,
                    t.status,
                    t.created_at,
                    t.updated_at
                FROM vk_tickets t
                JOIN vk_users u ON u.id = t.user_id
                WHERE u.vk_id = ?
                ORDER BY t.id DESC
                LIMIT ?
            """, (vk_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_server_status(self) -> dict[str, Any]:
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT id, status_code, status_text, updated_at
                FROM server_status
                WHERE id = 1
            """)
            row = cursor.fetchone()

            if row is None:
                return {
                    "status_code": "ok",
                    "status_text": "Сервер работает в обычном режиме.",
                    "updated_at": None,
                }

            return dict(row)