import asyncio
from os import getenv
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import logging

from app.handlers.universal import universal_router


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

root_router = Router()
root_router.include_router(universal_router)

async def main() -> None:
    BOT_TOKEN = getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в .env!")
        return
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(root_router)
    logger.info("Бот запущен. Ожидание событий...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())
