import asyncio
from aiogram import Bot
from database.requests import get_servers
from utils import ping_ip
from config import ADMIN_ID

async def start_monitoring(bot: Bot):
    """
    Бесконечный цикл проверки серверов.
    Запускается один раз при старте бота.
    """
    while True:
        # Получаем список серверов
        servers = await get_servers()

        # Проверяем каждый
        for server in servers:

            # Если сервер упал - шлём аларм!
            is_online = await ping_ip(server.ip)
            if not is_online:
                alert_text = (
                    f"🚨 <b>ALARM! Сервер упал!</b>\n\n"
                    f"🔻 Имя: <b>{server.name}</b>\n"
                    f"🔻 IP: <code>{server.ip}</code>"
                )
                try:
                    await bot.send_message(chat_id=ADMIN_ID, text=alert_text)
                except Exception as e:
                    print(f"Не удалось отправить алерт: {e}")
        
        # 3. Спим 60 секунд перед следующей проверкой
        # Важно: используем asyncio.sleep, а не time.sleep!
        await asyncio.sleep(10)