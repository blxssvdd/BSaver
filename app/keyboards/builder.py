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

def build_quality_keyboard(formats: list, short_id: str, source: str, audio_items=None) -> InlineKeyboardMarkup:
    buttons = []
    best_by_height = {}
    for fmt in formats:
        height = fmt.get('height')
        if not height or height not in MAIN_HEIGHTS:
            continue
        if height > 1080:
            continue
        if height not in best_by_height or (fmt.get('size') and fmt.get('size') > (best_by_height[height].get('size') or 0)):
            best_by_height[height] = fmt
    for h in MAIN_HEIGHTS:
        fmt = best_by_height.get(h)
        if not fmt:
            continue
        label = f"{h}p"
        buttons.append(
            InlineKeyboardButton(
                text=label,
                callback_data=f"download:{source}:{short_id}:{h}"
            )
        )
    # MP3 кнопка с эмодзи нотки
    mp3_text = "🎵 MP3"
    buttons.append(
        InlineKeyboardButton(
            text=mp3_text,
            callback_data=f"download:{source}:{short_id}:mp3"
        )
    )
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+3] for i in range(0, len(buttons), 3)])