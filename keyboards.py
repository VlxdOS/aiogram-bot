# keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- ГЛАВНОЕ МЕНЮ ---
main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        # Ряд 1: Основные функции (которые у нас уже есть в handlers.py)
        [
            InlineKeyboardButton(text="📋 Список", callback_data="cmd_list"),
            InlineKeyboardButton(text="🚀 Проверить всё", callback_data="cmd_check_all")
        ],
        # Ряд 2: Системные метрики (скелет на будущее)
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="cmd_stats"),
            InlineKeyboardButton(text="💾 Disk / CPU", callback_data="cmd_load")
        ],
        # Ряд 3: Утилиты (скелет)
        [
            InlineKeyboardButton(text="🔑 Пароль", callback_data="cmd_genpass"),
            InlineKeyboardButton(text="🆘 Поддержка", callback_data="cmd_support")
        ]
    ]
)

# --- МЕНЮ ОТМЕНЫ ---
# Пригодится, когда будем делать диалоги (FSM)
cancel_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cmd_cancel")]
    ]
)