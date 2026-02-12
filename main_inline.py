import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers import router

# Включаем логирование (чтобы видеть в консоли, что происходит)
logging.basicConfig(level=logging.INFO)

# 1. Создаем объект бота
bot = Bot(token=BOT_TOKEN)

# 2. Создаем диспетчер (мозг)
dp = Dispatcher()

dp.include_router(router)

# --- ЗАПУСК ---
async def main():
    print("Бот запускается...")
    # Удаляем вебхуки (на всякий случай, чтобы не было конфликтов)
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем бесконечный опрос серверов Telegram
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())