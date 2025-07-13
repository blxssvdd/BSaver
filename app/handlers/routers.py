from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в BSaver!\n\n"
        "Я помогу быстро и удобно скачать видео или музыку с YouTube прямо в Telegram.\n"
        "Просто отправь мне ссылку на ролик — и получи нужный файл без лишних шагов.\n\n"
        "Для подробностей и возможностей — команда /help."
    )

@router.message(F.text == "/help")
async def cmd_help(message: Message):
    await message.answer(
        "BSaver — твой быстрый способ сохранить YouTube-видео и музыку!\n\n"
        "Что я умею:\n"
        "• Скачиваю видео и аудио с YouTube;\n"
        "• Поддерживаю различные качества видео;\n"
        "• Отправляю файлы максимально быстро;\n"
        "• Работаю как в личных, так и в групповых чатах;\n"
        "• Позволяю настраивать параметры под себя.\n\n"
        "💡 Просто пришли ссылку на YouTube — и выбери нужный формат!\n\n"
        "Поддержать развитие:\n"
        "🇺🇦 UAH: https://donatello.to/blvssxdv\n"
        "💎 USDT: https://t.me/send?start=IVhodMgcffYp"
    )

@router.message(F.text == "/privacy")
async def cmd_privacy(message: Message):
    await message.answer(
        "🔒 Приватность с BSaver\n\n"
        "Мы ценим вашу анонимность и не собираем лишних данных.\n\n"
        "Что сохраняется:\n"
        "- Только ID чата для работы настроек;\n"
        "- Анонимная информация о загрузках (ID или ссылка на ролик, ID файла Telegram) — чтобы ускорить скачивание для всех. Эти данные не связаны с вашим аккаунтом и удаляются автоматически.\n\n"
        "Что НЕ сохраняется:\n"
        "- Личные данные профиля, история сообщений и загрузок;\n"
        "- Информация о ваших страницах в других сервисах;\n"
        "- Всё, что не нужно для работы бота.\n\n"
        "Удалить свои данные просто:\n"
        "- В личном чате — заблокируйте бота;\n"
        "- Анонимные данные удаляются автоматически раз в 1-2 месяца."
    )

@router.message(F.text == "/feedback")
async def cmd_feedback(message: Message):
    await message.answer(
        "💬 Есть идея, вопрос или нашли баг?\n"
        "Свяжитесь с поддержкой: @BSaverSupportbot\n\n"
        "Мы всегда открыты для обратной связи!"
    )
