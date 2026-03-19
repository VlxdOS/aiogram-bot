import asyncio
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery 

# Импорты БД
from sqlalchemy.exc import IntegrityError
from database.core import async_session_maker
from database.models import Server
from database.requests import get_servers

# Импорт утилит и кнопок
from utils import ping_ip
from keyboards import main_menu 

router = Router()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

async def format_server_status(server):
    """
    Пингует сервер и возвращает строку для отчета.
    Используется внутри /check_all для asyncio.gather
    """
    is_online = await ping_ip(server.ip)
    status_icon = "✅" if is_online else "❌"
    # Форматируем строку (HTML теги работают, т.к. мы включили их в main.py)
    return f"{status_icon} <b>{server.name}</b> (<code>{server.ip}</code>)\n"

# --- ХЭНДЛЕРЫ ---

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Привет, Админ!</b>\n\n"
        "Доступные команды:\n"
        "/add IP Name - Добавить сервер\n"
        "/list - Список серверов\n"
        "/check_all - Проверить состояние всех",
        reply_markup=main_menu # 👈 ПРИКРЕПЛЯЕМ КНОПКИ СЮДА
    )

@router.message(Command("add"))
async def add_server_handler(message: types.Message):
    # Разбираем сообщение: /add 8.8.8.8 Google DNS
    try:
        # maxsplit=2 позволяет имени содержать пробелы
        _, ip, name = message.text.split(maxsplit=2)
    except ValueError:
        await message.answer("⚠️ <b>Формат:</b> <code>/add IP Название</code>")
        return

    # Запись в БД
    try:
        async with async_session_maker() as session:
            new_server = Server(ip=ip, name=name)
            session.add(new_server)
            await session.commit()
            
        await message.answer(f"✅ Сервер <b>{name}</b> ({ip}) сохранен!")
        
    except IntegrityError:
        await message.answer("⛔ Такой IP уже есть в базе.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@router.message(Command("list"))
@router.callback_query(F.data == "cmd_list")
async def cmd_list(event: Message | CallbackQuery):
    # Если это кнопка, нам нужно ответить на callback (чтобы часики пропали)
    if isinstance(event, CallbackQuery):
        await event.answer()
        message = event.message # Получаем объект сообщения из кнопки
    else:
        message = event

    # Дальше логика та же...
    servers = await get_servers()
    # ... (твой код вывода списка) ...
    if not servers:
        await message.answer("📭 Список серверов пуст.")
        return
        
    response_text = "🖥 <b>Список серверов:</b>\n\n"
    for server in servers:
        response_text += f"🔹 <b>{server.name}</b>: <code>{server.ip}</code>\n"
    
    await message.answer(response_text)

@router.message(Command("check_all"))
@router.callback_query(F.data == "cmd_check_all")
async def cmd_check_all(event: Message | CallbackQuery):
    if isinstance(event, CallbackQuery):
        await event.answer()
        message = event.message
    else:
        message = event

    servers = await get_servers()
    
    if not servers:
        await message.answer("📭 Нечего проверять, база пуста.")
        return

    status_msg = await message.answer("⏳ <b>Пингую серверы...</b>")

    # Создаем список задач (Tasks)
    tasks = [format_server_status(server) for server in servers]

    # Запускаем все пинги параллельно
    results = await asyncio.gather(*tasks)

    # Собираем отчет
    report = "📊 <b>Отчет о состоянии:</b>\n\n" + "".join(results)
    
    # Редактируем старое сообщение, чтобы не спамить
    await status_msg.edit_text(report)

# Эхо-хэндлер для всего остального
@router.message()
async def echo_handler(message: types.Message):
    await message.answer("Не понимаю команду. Используй /start")