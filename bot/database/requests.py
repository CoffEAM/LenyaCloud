from bot.database.db import get_connection


def get_internal_user_id(telegram_id: int) -> int | None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = cursor.fetchone()
        return row["id"] if row else None


def has_used_trial(telegram_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT has_used_trial FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return False
        return bool(row["has_used_trial"])


def has_active_new_key_request(telegram_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT r.id
            FROM requests r
            JOIN users u ON u.id = r.user_id
            WHERE u.telegram_id = ?
              AND r.request_type = 'new_key'
              AND r.status IN ('new', 'in_progress')
            LIMIT 1
        """, (telegram_id,))
        row = cursor.fetchone()
        return row is not None


def has_active_renewal_request(telegram_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT r.id
            FROM requests r
            JOIN users u ON u.id = r.user_id
            WHERE u.telegram_id = ?
              AND r.request_type = 'renewal'
              AND r.status IN ('new', 'in_progress')
            LIMIT 1
        """, (telegram_id,))
        row = cursor.fetchone()
        return row is not None


def create_new_key_request(
    telegram_id: int,
    plan_type: str,
    days_count: int,
    amount_rub: int,
    payment_status: str,
    payment_proof_file_id: str | None,
    payment_proof_type: str | None,
    comment: str | None,
) -> int:
    user_id = get_internal_user_id(telegram_id)
    if user_id is None:
        raise ValueError("Пользователь не найден в базе")

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO requests (
                user_id,
                request_type,
                plan_type,
                days_count,
                amount_rub,
                payment_status,
                payment_proof_file_id,
                payment_proof_type,
                comment,
                status,
                updated_at
            )
            VALUES (?, 'new_key', ?, ?, ?, ?, ?, ?, ?, 'new', CURRENT_TIMESTAMP)
        """, (
            user_id,
            plan_type,
            days_count,
            amount_rub,
            payment_status,
            payment_proof_file_id,
            payment_proof_type,
            comment,
        ))
        request_id = cursor.lastrowid
        connection.commit()
        return int(request_id)


def create_renewal_request(
    telegram_id: int,
    plan_type: str,
    days_count: int,
    amount_rub: int,
    payment_status: str,
    payment_proof_file_id: str | None,
    payment_proof_type: str | None,
    comment: str | None,
) -> int:
    user_id = get_internal_user_id(telegram_id)
    if user_id is None:
        raise ValueError("Пользователь не найден в базе")

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO requests (
                user_id,
                request_type,
                plan_type,
                days_count,
                amount_rub,
                payment_status,
                payment_proof_file_id,
                payment_proof_type,
                comment,
                status,
                updated_at
            )
            VALUES (?, 'renewal', ?, ?, ?, ?, ?, ?, ?, 'new', CURRENT_TIMESTAMP)
        """, (
            user_id,
            plan_type,
            days_count,
            amount_rub,
            payment_status,
            payment_proof_file_id,
            payment_proof_type,
            comment,
        ))
        request_id = cursor.lastrowid
        connection.commit()
        return int(request_id)


def mark_trial_as_used(telegram_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE users
            SET has_used_trial = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
        """, (telegram_id,))
        connection.commit()


def get_request_by_id(request_id: int) -> dict | None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                r.id,
                r.user_id,
                r.request_type,
                r.plan_type,
                r.days_count,
                r.amount_rub,
                r.payment_status,
                r.payment_proof_file_id,
                r.payment_proof_type,
                r.comment,
                r.status,
                r.created_at,
                r.updated_at,
                u.telegram_id,
                u.username,
                u.first_name,
                u.last_name,
                u.full_name
            FROM requests r
            JOIN users u ON u.id = r.user_id
            WHERE r.id = ?
        """, (request_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_requests_by_type(request_type: str, statuses: tuple[str, ...] = ("new", "in_progress")) -> list[dict]:
    placeholders = ",".join("?" for _ in statuses)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(f"""
            SELECT
                r.id,
                r.user_id,
                r.request_type,
                r.plan_type,
                r.days_count,
                r.amount_rub,
                r.payment_status,
                r.payment_proof_file_id,
                r.payment_proof_type,
                r.comment,
                r.status,
                r.created_at,
                r.updated_at,
                u.telegram_id,
                u.username,
                u.first_name,
                u.last_name,
                u.full_name
            FROM requests r
            JOIN users u ON u.id = r.user_id
            WHERE r.request_type = ?
              AND r.status IN ({placeholders})
            ORDER BY r.created_at ASC
        """, (request_type, *statuses))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_new_key_requests(statuses: tuple[str, ...] = ("new", "in_progress")) -> list[dict]:
    return get_requests_by_type("new_key", statuses)


def get_renewal_requests(statuses: tuple[str, ...] = ("new", "in_progress")) -> list[dict]:
    return get_requests_by_type("renewal", statuses)


def update_request_status(request_id: int, new_status: str) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE requests
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, request_id))
        connection.commit()