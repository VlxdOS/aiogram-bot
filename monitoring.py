import asyncio
from datetime import datetime
from aiogram import Bot

from database.requests import get_servers
from utils import ping_ip
from config import ADMIN_ID

# Словарь для хранения времени падения: { "192.168.1.1": datetime_object }
down_times = {}

# Словарь для хранения прошлого состояния: { "192.168.1.1": True/False }
last_states = {}

async def start_monitoring(bot: Bot):
    """
    Фоновый процесс.
    Отправляет отчет ТОЛЬКО если статус хотя бы одного сервера изменился.
    """
    print("👀 Умный мониторинг запущен...")
    
    # Делаем глобальными, чтобы они сохранялись между циклами while
    global down_times, last_states

    while True:
        try:
            servers = await get_servers()
            
            if servers:
                # 1. Пингуем ВСЕ серверы параллельно
                # Создаем задачи
                tasks = [ping_ip(server.ip) for server in servers]
                # Запускаем и получаем список True/False (в том же порядке, что и servers)
                results = await asyncio.gather(*tasks)
                
                # 2. Формируем текущее состояние: { "IP": True/False }
                current_states = {}
                # zip объединяет список серверов и результаты пинга в пары
                for server, is_online in zip(servers, results):
                    current_states[server.ip] = is_online

                # 3. ПРОВЕРЯЕМ: ИЗМЕНИЛОСЬ ЛИ ЧТО-ТО?
                # Сравниваем словари текущего и прошлого состояния
                if current_states != last_states:
                    
                    # Если это первый запуск, last_states пустой -> бот пришлет начальный отчет
                    # Если не первый -> значит что-то упало или поднялось

                    # Обновляем таймеры падения
                    for server in servers:
                        is_online = current_states[server.ip]
                        
                        if not is_online:
                            # Если сервер упал и его нет в списке упавших -> записываем время
                            if server.ip not in down_times:
                                down_times[server.ip] = datetime.now()
                        else:
                            # Если сервер онлайн, убираем его из списка упавших (если он там был)
                            if server.ip in down_times:
                                del down_times[server.ip]

                    # 4. ФОРМИРУЕМ ОТЧЕТ
                    # Сначала собираем списки для текста
                    down_text = ""
                    up_text = ""
                    
                    for server in servers:
                        is_online = current_states[server.ip]
                        
                        if not is_online:
                            # Считаем, сколько времени лежит
                            start_time = down_times.get(server.ip, datetime.now())
                            # Форматируем время в строку ЧЧ:ММ:СС
                            time_str = start_time.strftime("%H:%M:%S")
                            down_text += f"🔴 <b>{server.name}</b> ({server.ip}) — 🕒 с {time_str}\n"
                        else:
                            up_text += f"🟢 <b>{server.name}</b> ({server.ip})\n"

                    # Собираем итоговое сообщение
                    report = "🔔 <b>Обновление статуса серверов</b>\n\n"
                    
                    if down_text:
                        report += "<b>❌ НЕДОСТУПНЫЕ:</b>\n\n" + down_text + "\n"
                    
                    if up_text:
                        report += "<b>✅ РАБОТАЮТ:</b>\n\n" + up_text

                    # Отправляем админу
                    try:
                        await bot.send_message(chat_id=ADMIN_ID, text=report)
                    except Exception as e:
                        print(f"Ошибка отправки сообщения: {e}")
                    
                    # 5. ЗАПОМИНАЕМ ТЕКУЩЕЕ СОСТОЯНИЕ
                    # copy() нужен, чтобы сохранить значения, а не ссылку на словарь
                    last_states = current_states.copy()

        except Exception as e:
            print(f"Ошибка в цикле мониторинга: {e}")

        # Пауза перед следующей проверкой (например, 30 секунд)
        await asyncio.sleep(30)