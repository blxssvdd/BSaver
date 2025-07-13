import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import BOT_TOKEN
from app.handlers import routers, youtube

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("BOT")


async def set_commands(bot):
    commands = [
        BotCommand(command="help", description="Справка и возможности"),
        BotCommand(command="privacy", description="Политика приватности"),
        BotCommand(command="feedback", description="Обратная связь"),
    ]
    await bot.set_my_commands(commands)


async def main():
    logger.info("🟢 Бот запускается...")
    if not BOT_TOKEN or not isinstance(BOT_TOKEN, str):
        logger.critical("❌ BOT_TOKEN не найден! Укажите переменную окружения BOT_TOKEN.")
        return
    try:
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        dp.include_routers(routers.router, youtube.router)
        await set_commands(bot)
        logger.info("🔄 Бот готов к работе. Ожидаем сообщения...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"🔴 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        raise
    finally:
        logger.info("Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())