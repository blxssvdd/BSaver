from aiogram import Router, types
import re
import logging
import yt_dlp
from app.keyboards import build_formats_keyboard
from app.utils.link_storage import link_storage
from aiogram.types import FSInputFile

logger = logging.getLogger(__name__)

universal_router = Router()

YOUTUBE_REGEX = re.compile(r"https?://(www\.)?(youtube\.com|youtu\.be)/[\w\-/?=&#.]+", re.IGNORECASE)
TIKTOK_REGEX = re.compile(r"https?://(www\.)?tiktok\.com/[\w\-/?=&#.]+", re.IGNORECASE)

FFMPEG_PATH = r"D:/Programming/Приложения/ffmpeg-7.1.1-full_build/bin"

@universal_router.message()
async def handle_any_link(message: types.Message):
    text = message.text or ""
    if YOUTUBE_REGEX.search(text):
        await process_youtube(message, text)
    elif TIKTOK_REGEX.search(text):
        await process_tiktok(message, text)
    else:
        await message.answer("Пожалуйста, отправьте ссылку на видео YouTube или TikTok.")

async def process_youtube(message: types.Message, url: str):
    await message.answer("🔎 Получаю информацию о видео...")
    try:
        ydl_opts = {"quiet": True, "skip_download": True, "format": "bestvideo+bestaudio/best", "ffmpeg_location": FFMPEG_PATH}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        title = info.get("title", "Видео")
        thumb = info.get("thumbnail")
        POPULAR_RES = [144, 240, 360, 480, 720, 1080, 1440, 2160]
        best_formats = {}
        # Сначала ищем с аудио, если нет — берём video-only
        for f in info.get("formats", []):
            if f.get("height") and f.get("vcodec") != "none":
                height = int(f['height'])
                ext = f.get('ext', '')
                if ext not in ("mp4", "webm"):
                    continue
                if height in POPULAR_RES and height not in best_formats:
                    best_formats[height] = {
                        "label": f"{height}p",
                        "format_id": f["format_id"],
                        "ext": ext
                    }
        formats = [best_formats[h] for h in POPULAR_RES if h in best_formats]
        # Если ничего не найдено — ищем video-only
        if not formats:
            for f in info.get("formats", []):
                if f.get("height") and f.get("vcodec") != "none":
                    height = int(f['height'])
                    ext = f.get('ext', '')
                    if ext not in ("mp4", "webm"):
                        continue
                    if height in POPULAR_RES and height not in best_formats:
                        best_formats[height] = {
                            "label": f"{height}p (video-only)",
                            "format_id": f["format_id"],
                            "ext": ext
                        }
            formats = [best_formats[h] for h in POPULAR_RES if h in best_formats]
        kb = build_formats_keyboard(formats, url, has_mp3=True, has_preview=bool(thumb))
        text = f"<b>{title}</b>\n\nФорматы для скачивания ↓"
        if thumb:
            await message.answer_photo(thumb, caption=text, parse_mode="HTML", reply_markup=kb)
        else:
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.exception(e)
        await message.answer("Ошибка при получении информации о видео.")

# Заглушка для TikTok, чтобы не было ошибки
async def process_tiktok(message, text):
    await message.answer("TikTok поддержка будет добавлена позже.")

@universal_router.callback_query()
async def download_callback(call: types.CallbackQuery):
    data = call.data
    message = call.message
    try:
        if data.startswith("yt_") or data.startswith("mp3") or data.startswith("preview"):
            parts = data.split("|", 1)
            action = parts[0]
            link_id = parts[1] if len(parts) > 1 else None
            url = link_storage.get(link_id) if link_id else None
            if not url:
                await call.message.answer("Ошибка: не удалось получить ссылку.")
                return
            if action.startswith("yt_"):
                format_id = action[3:]
                await call.answer("Скачиваю выбранный формат...")
                ydl_opts = {
                    "format": f"{format_id}+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "outtmpl": "video.%(ext)s",
                    "quiet": True,
                    "ffmpeg_location": FFMPEG_PATH
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    file_path = ydl.prepare_filename(info)
                import os
                file_size = os.path.getsize(file_path)
                file = FSInputFile(file_path)
                # Если файл больше 50 МБ — отправляем как документ
                if file_size > 49 * 1024 * 1024:
                    await call.message.answer_document(file, caption=info.get("title", "Видео"))
                else:
                    await call.message.answer_video(file, caption=info.get("title", "Видео"))
                os.remove(file_path)
            elif action == "mp3":
                await call.answer("Скачиваю MP3...")
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": "audio.%(ext)s",
                    "quiet": True,
                    "ffmpeg_location": FFMPEG_PATH,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    file_path = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
                file = FSInputFile(file_path, filename=info.get("title", "audio") + ".mp3")
                await call.message.answer_document(file, caption=info.get("title", "Аудио"))
                import os
                os.remove(file_path)
            elif action == "preview" and url:
                ydl_opts = {"quiet": True, "skip_download": True, "format": "bestvideo+bestaudio/best", "ffmpeg_location": FFMPEG_PATH}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                thumb = info.get("thumbnail")
                if thumb:
                    await call.message.answer_photo(thumb, caption="Превью видео")
                else:
                    await call.message.answer("Превью недоступно.")
        else:
            await call.answer("Неизвестная команда.")
    except Exception as e:
        logger.exception(e)
        await call.message.answer("Ошибка при скачивании файла.")
