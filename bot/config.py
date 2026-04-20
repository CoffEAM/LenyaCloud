import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class TgBot:
    token: str
    admins: list[int]


@dataclass
class PaymentConfig:
    card_number: str
    card_holder: str


@dataclass
class LinksConfig:
    vk_group_link: str


@dataclass
class Config:
    tg_bot: TgBot
    payment: PaymentConfig
    links: LinksConfig


def parse_admins(admins_raw: str) -> list[int]:
    if not admins_raw.strip():
        return []

    result = []
    for admin_id in admins_raw.split(","):
        admin_id = admin_id.strip()
        if admin_id:
            result.append(int(admin_id))
    return result


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    admins_raw = os.getenv("ADMINS", "").strip()
    card_number = os.getenv("CARD_NUMBER", "").strip()
    card_holder = os.getenv("CARD_HOLDER", "").strip()
    vk_group_link = os.getenv("VK_GROUP_LINK", "").strip()

    if not token:
        raise ValueError("Не найден BOT_TOKEN в .env")

    return Config(
        tg_bot=TgBot(
            token=token,
            admins=parse_admins(admins_raw),
        ),
        payment=PaymentConfig(
            card_number=card_number,
            card_holder=card_holder,
        ),
        links=LinksConfig(
            vk_group_link=vk_group_link,
        )
    )