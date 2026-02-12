from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Создаем кнопки
# Обрати внимание: теперь есть callback_data
btn_stat = InlineKeyboardButton(text="📊 Статистика", callback_data="cmd_stats")
btn_support = InlineKeyboardButton(text="🆘 Поддержка", callback_data="cmd_support")
btn_ping = InlineKeyboardButton(text="🌐 Пинг", callback_data="cmd_ping")
btn_cancel = InlineKeyboardButton(text="❌ Отмена", callback_data="cmd_cancel")

main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [btn_stat, btn_support], # Первый ряд (две кнопки вместе)
        [btn_ping] 
    ],
)

ping_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [btn_cancel], # Первый ряд (две кнопки вместе)
    ],
)