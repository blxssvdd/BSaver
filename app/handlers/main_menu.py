from aiogram import Router, types
from aiogram.filters import Command
from app.keyboards import main_menu

main_menu_router = Router()

@main_menu_router.message(Command(commands=["start", "help"]))
async def send_welcome(message: types.Message):
    await message.answer(
        "Привет! Я помогу скачать видео/аудио с TikTok и YouTube без водяных знаков.\nВыбери нужный сервис:",
        reply_markup=main_menu
    )

@main_menu_router.callback_query(lambda c: c.data == "tiktok")
async def process_tiktok(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Отправь ссылку на видео TikTok:")

@main_menu_router.callback_query(lambda c: c.data == "youtube")
async def process_youtube(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Отправь ссылку на видео YouTube:")
