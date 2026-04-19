from datetime import datetime, timedelta

from bot.database.db import get_connection
from bot.database.requests import get_internal_user_id


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def create_subscription_from_request(
    telegram_id: int,
    request_id: int,
    plan_type: str,
    days_count: int,
    access_text: str,
) -> int:
    user_id = get_internal_user_id(telegram_id)
    if user_id is None:
        raise ValueError("Пользователь не найден")

    now = datetime.now()

    starts_at = now.strftime(DATETIME_FORMAT)
    expires_at = (now + timedelta(days=days_count)).strftime(DATETIME_FORMAT)

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO subscriptions (
                user_id,
                request_id,
                status,
                plan_type,
                days_count,
                is_unlimited,
                starts_at,
                expires_at,
                access_text,
                updated_at
            )
            VALUES (?, ?, 'active', ?, ?, 0, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            user_id,
            request_id,
            plan_type,
            days_count,
            starts_at,
            expires_at,
            access_text,
        ))

        connection.commit()
        return int(cursor.lastrowid)


def create_manual_subscription(
    telegram_id: int,
    plan_type: str,
    days_count: int | None,
    access_text: str,
    is_unlimited: bool,
) -> int:
    user_id = get_internal_user_id(telegram_id)
    if user_id is None:
        raise ValueError("Пользователь не найден")

    now = datetime.now()
    starts_at = now.strftime(DATETIME_FORMAT)

    if is_unlimited:
        expires_at = None
    else:
        expires_at = (now + timedelta(days=days_count)).strftime(DATETIME_FORMAT)

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO subscriptions (
                user_id,
                status,
                plan_type,
                days_count,
                is_unlimited,
                starts_at,
                expires_at,
                access_text,
                updated_at
            )
            VALUES (?, 'active', ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            user_id,
            plan_type,
            days_count,
            int(is_unlimited),
            starts_at,
            expires_at,
            access_text,
        ))

        connection.commit()
        return int(cursor.lastrowid)


def get_latest_subscription_by_telegram_id(telegram_id: int) -> dict | None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT s.*
            FROM subscriptions s
            JOIN users u ON u.id = s.user_id
            WHERE u.telegram_id = ?
            ORDER BY s.id DESC
            LIMIT 1
        """, (telegram_id,))

        row = cursor.fetchone()
        return dict(row) if row else None


def get_active_subscription_by_telegram_id(telegram_id: int) -> dict | None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT s.*
            FROM subscriptions s
            JOIN users u ON u.id = s.user_id
            WHERE u.telegram_id = ?
              AND s.status = 'active'
            ORDER BY s.id DESC
            LIMIT 1
        """, (telegram_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def has_active_subscription(telegram_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT s.id
            FROM subscriptions s
            JOIN users u ON u.id = s.user_id
            WHERE u.telegram_id = ?
              AND s.status = 'active'
            LIMIT 1
        """, (telegram_id,))
        row = cursor.fetchone()
        return row is not None


def extend_active_subscription(
    telegram_id: int,
    days_count: int,
    access_text: str | None = None,
) -> int:
    subscription = get_active_subscription_by_telegram_id(telegram_id)
    if subscription is None:
        raise ValueError("Активная подписка не найдена")

    if subscription["is_unlimited"]:
        raise ValueError("Бессрочную подписку нельзя продлить по дням")

    now = datetime.now()
    expires_at_raw = subscription["expires_at"]
    expires_at = datetime.strptime(expires_at_raw, DATETIME_FORMAT)

    base_date = expires_at if expires_at > now else now
    new_expires_at = (base_date + timedelta(days=days_count)).strftime(DATETIME_FORMAT)

    with get_connection() as connection:
        cursor = connection.cursor()

        if access_text is None:
            cursor.execute("""
                UPDATE subscriptions
                SET expires_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                new_expires_at,
                subscription["id"],
            ))
        else:
            cursor.execute("""
                UPDATE subscriptions
                SET expires_at = ?,
                    access_text = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                new_expires_at,
                access_text,
                subscription["id"],
            ))

        connection.commit()
        return int(subscription["id"])


def mark_expired_subscriptions() -> None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE subscriptions
            SET status = 'expired',
                updated_at = CURRENT_TIMESTAMP
            WHERE is_unlimited = 0
              AND status = 'active'
              AND datetime(expires_at) <= datetime('now', 'localtime')
        """)

        connection.commit()

def has_unlimited_active_subscription(telegram_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT s.id
            FROM subscriptions s
            JOIN users u ON u.id = s.user_id
            WHERE u.telegram_id = ?
              AND s.status = 'active'
              AND s.is_unlimited = 1
            LIMIT 1
        """, (telegram_id,))
        row = cursor.fetchone()
        return row is not None