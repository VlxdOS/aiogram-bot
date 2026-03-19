import asyncio
import ipaddress
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery 

# Импорты БД
from sqlalchemy.exc import IntegrityError
from database.core import async_session_maker
from database.models import Server
from database.requests import get_servers, delete_server

# Импорт утилит
from utils import ping_ip, generate_password, get_system_load
from keyboards import main_menu

router = Router()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

async def format_server_status(server):
    is_online = await ping_ip(server.ip)
    status_icon = "🟢" if is_online else "🔴"
    return f"{status_icon} <b>{server.name}</b> (<code>{server.ip}</code>)\n"

# --- ОСНОВНЫЕ КОМАНДЫ ---

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Панель управления серверами</b>\n\n"
        "Выберите действие в меню или используйте команды:\n"
        "/add IP Name - Добавить\n"
        "/del IP - Удалить\n",
        reply_markup=main_menu
    )

@router.message(Command("add"))
async def add_server_handler(message: types.Message):
    try:
        # Разбиваем сообщение
        _, ip, name = message.text.split(maxsplit=2)
        
        # 👇 ДОБАВЛЯЕМ ПРОВЕРКУ IP
        # Если ip не валидный, эта строчка вызовет ошибку ValueError
        ipaddress.ip_address(ip) 
        
    except ValueError:
        await message.answer(
            "⚠️ <b>Ошибка формата!</b>\n\n"
            "Нужно: <code>/add IP Название</code>\n"
            "Пример: <code>/add 8.8.8.8 Google DNS</code>\n\n"
            "<i>Похоже, вы ввели некорректный IP или перепутали местами IP и Имя.</i>"
        )
        return

    # Если проверка прошла, пишем в базу
    try:
        async with async_session_maker() as session:
            new_server = Server(ip=ip, name=name)
            session.add(new_server)
            await session.commit()
        await message.answer(f"✅ Сервер <b>{name}</b> ({ip}) добавлен!")
    except IntegrityError:
        await message.answer("⛔ Такой IP уже есть.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

# Новая команда удаления
@router.message(Command("del"))
async def del_server_handler(message: types.Message):
    try:
        _, ip = message.text.split(maxsplit=1)
        ip = ip.strip() # <--- Убираем пробелы по краям
    except ValueError:
        await message.answer("⚠️ Пример: <code>/del 8.8.8.8</code>")
        return

    await delete_server(ip)
    await message.answer(f"🗑 Сервер с IP <code>{ip}</code> удален (если он был).")

# --- КНОПКИ ГЛАВНОГО МЕНЮ ---

# 1. Список серверов (List)
@router.message(Command("list"))
@router.callback_query(F.data == "cmd_list")
async def cmd_list(event: Message | CallbackQuery):
    if isinstance(event, CallbackQuery):
        await event.answer()
        message = event.message
    else:
        message = event

    servers = await get_servers()
    if not servers:
        await message.answer("📭 Список пуст.")
        return

    # Собираем текст. ВАЖНО: += добавляет строку к предыдущей
    text = "🖥 <b>Список серверов:</b>\n\n"
    for server in servers:
        text += f"🔹 <b>{server.name}</b>: <code>{server.ip}</code>\n"
    
    await message.answer(text)

# 2. Проверить всё (Check All)
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
        await message.answer("📭 База пуста.")
        return

    status_msg = await message.answer("⏳ <b>Проверка доступности...</b>")

    tasks = [format_server_status(server) for server in servers]
    results = await asyncio.gather(*tasks)
    
    # join склеивает список результатов в одну строку
    report = "📊 <b>Статус серверов:</b>\n\n" + "".join(results)
    
    await status_msg.edit_text(report)

# 3. Статистика (просто считаем количество)
@router.callback_query(F.data == "cmd_stats")
async def cmd_stats(callback: CallbackQuery):
    await callback.answer()
    servers = await get_servers()
    await callback.message.answer(f"📊 Всего серверов в базе: <b>{len(servers)}</b>")

# 4. Нагрузка (System Load)
@router.callback_query(F.data == "cmd_load")
async def cmd_load(callback: CallbackQuery):
    await callback.answer("Замеряю нагрузку...") # Показывает всплывашку сверху
    stats = get_system_load()
    await callback.message.answer(stats)

# 5. Генератор пароля
@router.callback_query(F.data == "cmd_genpass")
async def cmd_genpass(callback: CallbackQuery):
    await callback.answer()
    pwd = generate_password(10)
    await callback.message.answer(f"🔑 Твой пароль: <code>{pwd}</code>")

# 6. Поддержка
@router.callback_query(F.data == "cmd_support")
async def cmd_support(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("👨‍💻 По всем вопросам пиши @v1ad_shi1ov")

# Эхо
@router.message()
async def echo_handler(message: types.Message):
    await message.answer("Я не понимаю эту команду. Жми /start")