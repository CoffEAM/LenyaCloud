from bot.database.db import get_connection


def get_server_status() -> dict:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, status_code, status_text, updated_at
            FROM server_status
            WHERE id = 1
        """)
        row = cursor.fetchone()
        return dict(row)


def set_server_status(status_code: str, status_text: str) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE server_status
            SET status_code = ?,
                status_text = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (status_code, status_text))
        connection.commit()