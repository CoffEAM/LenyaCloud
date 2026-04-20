import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass
class VkConfig:
    group_token: str
    group_id: int
    db_path: Path
    tg_bot_token: str
    tg_admins: list[int]


def _parse_admins(raw_value: str) -> list[int]:
    if not raw_value.strip():
        return []

    result: list[int] = []
    for item in raw_value.split(","):
        item = item.strip()
        if item:
            result.append(int(item))
    return result


def load_vk_config() -> VkConfig:
    group_token = os.getenv("VK_GROUP_TOKEN", "").strip()
    group_id_raw = os.getenv("VK_GROUP_ID", "").strip()
    db_path_raw = os.getenv("BOT_DB_PATH", "bot.db").strip()
    tg_bot_token = os.getenv("BOT_TOKEN", "").strip()
    tg_admins_raw = os.getenv("ADMINS", "").strip()

    if not group_token:
        raise ValueError("Не найден VK_GROUP_TOKEN в .env")

    if not group_id_raw:
        raise ValueError("Не найден VK_GROUP_ID в .env")

    if not tg_bot_token:
        raise ValueError("Не найден BOT_TOKEN в .env")

    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / db_path_raw

    return VkConfig(
        group_token=group_token,
        group_id=int(group_id_raw),
        db_path=db_path,
        tg_bot_token=tg_bot_token,
        tg_admins=_parse_admins(tg_admins_raw),
    )