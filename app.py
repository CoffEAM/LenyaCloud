import asyncio
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from bot.main import main as run_telegram_bot
from vk_bot.main import run_vk_bot


async def main() -> None:
    await asyncio.gather(
        run_telegram_bot(),
        run_vk_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())