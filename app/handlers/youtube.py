import os
import logging
import tempfile
import time
import subprocess

from aiogram import Router, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.exceptions import TelegramEntityTooLarge

from app.services.youtube_service import YouTubeService


router = Router()
logger = logging.getLogger("YOUTUBE_HANDLER")

STANDARD_QUALITIES = ['144p', '240p', '360p', '480p', '720p']

def build_formats_keyboard(formats):
    video_formats = {f"{f.get('height')}p": f for f in formats.get('video', []) if f.get('height') and f.get('height') <= 720}
    keyboard = []
    row = []
    for quality in ['144p', '240p', '360p', '480p', '720p']:
        fmt = video_formats.get(quality)
        if fmt:
            row.append(InlineKeyboardButton(text=quality, callback_data=f"ytvideo_{fmt['format_id']}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="🎵 MP3", callback_data="ytaudio_mp3")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def build_formats_text(formats):
    video_formats = {f"{f.get('height')}p": f for f in formats.get('video', []) if f.get('height') and f.get('height') <= 720}
    available = []
    for quality in ['144p', '240p', '360p', '480p', '720p']:
        fmt = video_formats.get(quality)
        if fmt:
            size_mb = int(fmt.get('filesize', 0) or fmt.get('filesize_approx', 0) or 0) // (1024 * 1024)
            size_str = f"{size_mb} МБ" if size_mb else "? МБ"
            available.append(f"{quality} ({size_str})")
    return ', '.join(available)

def build_video_info_message(info, formats):
    title = info.get('title', 'YouTube Video')
    uploader = info.get('uploader', 'Unknown')
    uploader_url = info.get('uploader_url') or info.get('channel_url')
    duration = info.get('duration', 0)
    minutes = duration // 60
    seconds = duration % 60
    qualities = [
        ('144p', '🚀'),
        ('240p', '🚀'),
        ('360p', '🚀'),
        ('480p', '⚡️'),
        ('720p', '⚡️'),
    ]
    video_formats = {f"{f.get('height')}p": f for f in formats.get('video', []) if f.get('height') and f.get('height') <= 720}
    lines = []
    for q, emoji in qualities:
        fmt = video_formats.get(q)
        if fmt:
            size = int(fmt.get('filesize', 0) or fmt.get('filesize_approx', 0) or 0)
            size_mb = f"{size // (1024 * 1024)}MB" if size else "?MB"
            lines.append(f"{emoji} {q}: {size_mb}")
    lines_str = '\n'.join(lines)
    if uploader_url:
        uploader_line = f'👤 <a href="{uploader_url}">{uploader}</a>'
    else:
        uploader_line = f'👤 {uploader}'
    msg = (
        f"<b>{title}</b>\n"
        f"{uploader_line}\n"
        f"⏱ {minutes}:{seconds:02d}\n\n"
        f"{lines_str}\n\n"
        f"<i>Форматы для скачивания ↓</i>"
    )
    return msg

def reencode_mp4_for_telegram(input_path, output_path):
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-c:v', 'libx264', '-preset', 'fast', '-profile:v', 'main', '-level', '3.1',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        output_path
    ]
    subprocess.run(cmd, capture_output=True)

@router.message(F.text.contains("youtube.com") | F.text.contains("youtu.be"))
async def handle_youtube(message: Message):
    url = message.text
    try:
        wait_msg = await message.reply("👀 Получаю информацию о видео...")
        info = await YouTubeService.get_video_info(url)
        if not info or not info.get('formats'):
            await wait_msg.delete()
            await message.reply("❌ Не удалось получить информацию о видео. Проверьте ссылку.")
            return
        formats = YouTubeService.extract_video_audio_formats(info['formats'])
        video_formats = {f"{f.get('height')}p": f for f in formats.get('video', []) if f.get('height')}
        if not video_formats:
            await wait_msg.delete()
            await message.reply("❌ Не найдено подходящих видео-форматов для скачивания.")
            return
        msg = build_video_info_message(info, formats)
        kb = build_formats_keyboard(formats)
        thumbnail = info.get('thumbnail')
        if thumbnail:
            await message.reply_photo(thumbnail, caption=msg, reply_markup=kb, parse_mode="HTML")
        else:
            await message.reply(msg, reply_markup=kb, parse_mode="HTML")
        await wait_msg.delete()
    except Exception as e:
        logger.error(f"Ошибка YouTube: {e}")
        await message.reply(f"❌ Ошибка: {e}")

@router.callback_query(F.data.startswith("ytvideo_"))
async def process_video_format(callback: CallbackQuery):
    msg = getattr(callback, 'message', None)
    url = None
    if msg is not None:
        reply_msg = getattr(msg, 'reply_to_message', None)
        if reply_msg is not None and getattr(reply_msg, 'text', None):
            url = reply_msg.text
        elif hasattr(msg, 'caption') and msg.caption:
            url = msg.caption.split('\n')[0]
    data = getattr(callback, 'data', None)
    if not url or not isinstance(url, str) or not data or not isinstance(data, str) or not data.startswith("ytvideo_"):
        await callback.answer("Не удалось найти ссылку на видео.", show_alert=True)
        return
    url = str(url)
    format_id = data.replace("ytvideo_", "")
    await callback.answer("Скачиваю видео...")
    info = await YouTubeService.get_video_info(url)
    if not info:
        if msg:
            await msg.reply("❌ Не удалось получить информацию о видео.")
        return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
        temp_path = f.name
    success = await YouTubeService.download_format(url, format_id, temp_path)
    if not success:
        if msg:
            await msg.reply("❌ Не удалось скачать видео.")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return
    file_size = os.path.getsize(temp_path)
    if file_size == 0:
        if msg:
            await msg.reply("❌ Не удалось скачать видео: файл пустой. Попробуйте другой формат или ссылку.")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return
    tg_limit = 2 * 1024 * 1024 * 1024
    if file_size > tg_limit:
        if msg:
            await msg.reply("❗️ Файл слишком большой для отправки через Telegram (больше 2 ГБ).\nПопробуйте выбрать качество пониже!")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return
    title = info.get('title', 'YouTube Video')
    if msg:
        try:
            logger.info(f"Пробую отправить видео: {temp_path}, размер: {file_size} байт")
            try:
                with open(temp_path, 'rb') as f:
                    f.read(1024)
                logger.info("Файл доступен для чтения")
            except Exception as e:
                logger.error(f"Файл не доступен для чтения: {e}")
            await msg.reply_video(FSInputFile(temp_path, filename=f"{title[:50]}.mp4"), caption=f"Готово! {title}")
            logger.info("Видео успешно отправлено!")
        except TelegramEntityTooLarge:
            logger.warning("TelegramEntityTooLarge: пробую перекодировать файл")
            recoded_path = temp_path.replace('.mp4', '_tg.mp4')
            reencode_mp4_for_telegram(temp_path, recoded_path)
            try:
                await msg.reply_video(FSInputFile(recoded_path, filename=f"{title[:50]}_tg.mp4"), caption=f"Готово! {title}\n(перекодировано для Telegram)")
                logger.info("Перекодированное видео успешно отправлено!")
            except TelegramEntityTooLarge:
                logger.error("TelegramEntityTooLarge даже после перекодирования")
                await msg.reply("❗️ Файл не принят Telegram даже после перекодирования. Возможно, он не поддерживается. Попробуйте другой ролик или качество.")
            except Exception as e:
                logger.error(f"Ошибка при отправке перекодированного файла: {e}")
                await msg.reply(f"❌ Ошибка при отправке перекодированного файла: {e}")
            finally:
                if os.path.exists(recoded_path):
                    try:
                        os.remove(recoded_path)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Ошибка при отправке файла: {e}")
            await msg.reply(f"❌ Ошибка при отправке файла: {e}")
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except PermissionError:
            time.sleep(1)
            try:
                os.remove(temp_path)
            except Exception:
                pass

@router.callback_query(F.data == "ytaudio_mp3")
async def process_audio_mp3(callback: CallbackQuery):
    msg = getattr(callback, 'message', None)
    url = None
    if msg is not None:
        reply_msg = getattr(msg, 'reply_to_message', None)
        if reply_msg is not None and getattr(reply_msg, 'text', None):
            url = reply_msg.text
        elif hasattr(msg, 'caption') and msg.caption:
            url = msg.caption.split('\n')[0]
    if not url or not isinstance(url, str):
        await callback.answer("Не удалось найти ссылку на видео.", show_alert=True)
        return
    url = str(url)
    await callback.answer("Скачиваю MP3...")
    info = await YouTubeService.get_video_info(url)
    if not info:
        if msg:
            await msg.reply("❌ Не удалось получить информацию о видео.")
        return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        temp_path = f.name
    success = await YouTubeService.download_audio_mp3(url, temp_path)
    if not success:
        if msg:
            await msg.reply("❌ Не удалось скачать MP3.")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return
    file_size = os.path.getsize(temp_path)
    if file_size == 0:
        if msg:
            await msg.reply("❌ Не удалось скачать MP3: файл пустой. Попробуйте другой формат или ссылку.")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return
    tg_limit = 2 * 1024 * 1024 * 1024
    if file_size > tg_limit:
        if msg:
            await msg.reply("❗️ Файл слишком большой для отправки через Telegram (больше 2 ГБ).\nПопробуйте выбрать качество пониже!")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return
    title = info.get('title', 'YouTube Audio')
    duration = info.get('duration', 0)
    minutes = duration // 60
    seconds = duration % 60
    if msg:
        try:
            await msg.reply_audio(
                FSInputFile(temp_path, filename=f"{title[:50]}.mp3"),
                caption=f"Готово! {title}\n⏱ {minutes}:{seconds:02d}"
            )
        except TelegramEntityTooLarge:
            await msg.reply("❗️ Файл слишком большой для отправки через Telegram (ограничение сервера).\nПопробуйте выбрать качество пониже!")
        except Exception as e:
            await msg.reply(f"❌ Ошибка при отправке файла: {e}")
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except PermissionError:
            time.sleep(1)
            try:
                os.remove(temp_path)
            except Exception:
                pass