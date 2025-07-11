from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.utils.link_storage import link_storage

# Список поддерживаемых разрешений
RESOLUTIONS = ["144p", "240p", "360p", "480p", "720p", "1080p"]

# Формируем клавиатуру только с реально доступными форматами
def build_formats_keyboard(formats: list, video_url: str, has_mp3: bool = True, has_preview: bool = False) -> InlineKeyboardMarkup:
    rows = []
    link_id = link_storage.add(video_url)
    # Кнопки только для популярных разрешений, по одному в ряд
    for f in formats:
        res = f['label']
        fmt_id = f['format_id']
        icon = "📹"
        btn = InlineKeyboardButton(text=f"{icon} {res}", callback_data=f"yt_{fmt_id}|{link_id}")
        rows.append([btn])
    # Нижний ряд: MP3 и Превью
    bottom_row = []
    if has_mp3:
        bottom_row.append(InlineKeyboardButton(text="🎵 MP3", callback_data=f"mp3|{link_id}"))
    if has_preview:
        bottom_row.append(InlineKeyboardButton(text="🖼️ Превью", callback_data=f"preview|{link_id}"))
    if bottom_row:
        rows.append(bottom_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Скачать с TikTok', callback_data='tiktok'),
            InlineKeyboardButton(text='Скачать с YouTube', callback_data='youtube')
        ],
        [
            InlineKeyboardButton(text='Поддержать автора', url='https://t.me/blxssvdd')
        ]
    ]
)
