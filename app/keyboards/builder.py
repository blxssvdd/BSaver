from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

MAIN_HEIGHTS = [144, 240, 360, 480, 720, 1080]

def _format_size(size):
    if not size:
        return "?"
    for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} ПБ"

def build_quality_keyboard(formats: list, short_id: str, source: str) -> InlineKeyboardMarkup:
    buttons = []
    best_by_height = {}
    for fmt in formats:
        height = fmt.get('height')
        if not height or height not in MAIN_HEIGHTS:
            continue
        if height > 1080:
            continue
        if height not in best_by_height or (fmt.get('filesize') and fmt.get('filesize') > (best_by_height[height].get('filesize') or 0)):
            best_by_height[height] = fmt
    for h in MAIN_HEIGHTS:
        fmt = best_by_height.get(h)
        if not fmt:
            continue
        text = f"{h}p ({_format_size(fmt.get('filesize'))})"
        buttons.append(
            InlineKeyboardButton(
                text=text,
                callback_data=f"download:{source}:{short_id}:{h}"
            )
        )
    buttons.append(
        InlineKeyboardButton(
            text="🎵 MP3",
            callback_data=f"download:{source}:{short_id}:mp3"
        )
    )
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+3] for i in range(0, len(buttons), 3)])