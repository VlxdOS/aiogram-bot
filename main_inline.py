import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импортируем настройки из конфига (добавь туда PROXY_URL)
from config import BOT_TOKEN, PROXY_URL 
from handlers import router
from monitoring import start_monitoring

from database.core import engine, Base
# from database.models import Server # Можно убрать, если models импортируется внутри handlers или requests

# Настройка логирования
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def init_db():
    """Создает таблицы в БД, если их нет"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    print("🚀 Запуск бота...")

    # 1. Инициализация БД
    await init_db()

    # 2. Настройка сессии (Прокси)
    session = AiohttpSession(proxy=PROXY_URL)

    # 3. Создание бота
    # Включаем HTML глобально для всех сообщений
    bot = Bot(
        token=BOT_TOKEN, 
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # 4. Создание диспетчера
    dp = Dispatcher()
    dp.include_router(router)

    # Удаляем старые апдейты, чтобы бот не отвечал на сообщения, пришедшие пока он спал
    await bot.delete_webhook(drop_pending_updates=True)
    
    
    # 👇 ЗАПУСКАЕМ МОНИТОРИНГ В ФОНЕ
    # create_task создает "ответвление", которое работает само по себе
    asyncio.create_task(start_monitoring(bot))

    # Погнали!
    print("✅ Бот работает!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен")