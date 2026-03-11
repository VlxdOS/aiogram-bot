import ipaddress
import asyncio
import platform
import psutil

from aiogram import types, F, Router
from aiogram.filters.command import Command
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import aiohttp
import random, string

from config import ADMIN_ID

from keyboards import main_menu
from keyboards import ping_menu

router = Router()

class PingStates(StatesGroup):
    waiting_for_ip = State()

class GenPassStates(StatesGroup):
    waiting_for_len = State()

async def real_ping(ip_address: str) -> bool:
    """
    Асинхронно пингует IP. Возвращает True, если хост доступен.
    """
    # Определяем параметры пинга в зависимости от ОС
    # -n 1 (Windows) или -c 1 (Linux/Mac) - количество пакетов
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    # Запускаем процесс пинга в системе
    # stdout=asyncio.subprocess.DEVNULL означает "не выводи текст пинга в консоль бота"
    process = await asyncio.create_subprocess_shell(
        f"ping {param} 1 {ip_address}",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    
    # Ждем завершения процесса
    await process.wait()
    
    # Если код возврата 0 -> Успех. Если 1 или другое -> Ошибка.
    return process.returncode == 0

async def check_disk_space() -> str:
    DISK = "C:"
    free = psutil.disk_usage(DISK).free/(1024*1024*1024)

    return f"{free:.2f} Gb свободно на диске {DISK}"

async def load_cpu_ram() -> str:
    loop = asyncio.get_running_loop()

    cpu_usage = await loop.run_in_executor(None, psutil.cpu_percent, 1)
    ram_usage = psutil.virtual_memory()

    return f"CPU: {cpu_usage} %\nRam: {ram_usage[2]} % ({round(ram_usage[3]/1024**3, 1)} / {round(ram_usage[0]/1024**3, 1)})"

# Команда /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID or message.from_user.username == "NastyaSmolentseva":
        await message.answer("Привет, Админ!", reply_markup=main_menu)
    else:
        await message.answer("Привет, юзер!")

# Обработка кнопки "Проверка диска"
@router.callback_query(F.data == "cmd_check_disk")
async def check_disk(callback: CallbackQuery):
    await callback.answer()
    result = await check_disk_space()
    await callback.message.answer(f"Вывод: {result}")

# Обработка кнопки "Нагрузка"
@router.callback_query(F.data == "cmd_load")
async def cpu_load(callback: CallbackQuery):
    await callback.answer()
    result = await load_cpu_ram()
    await callback.message.answer(f"{result}")

# Генератор паролей
@router.message(Command("genpass"))
async def genpass(message: types.Message):
    args = message.text.split()

    if len(args) == 1:
        length = 12
    elif len(args) > 1:
        try:
            length = int(args[1])
        except ValueError:
            await message.answer("Ошибка! Длина должна быть числом!")
            return
    
    chars = string.ascii_letters + string.digits
    password = ''.join(random.choice(chars) for _ in range(length))
    
    await message.answer(f"Вот ваш пароль: `{password}`", parse_mode="Markdown")

# Обработка кнопки "Генерация пароля"
@router.callback_query(F.data == "cmd_genpass")
async def stat_genpass(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите длину пароля:", reply_markup=ping_menu)
    # Бот теперь ждет длину
    await state.set_state(GenPassStates.waiting_for_len)

# Обработка длины пароля
@router.message(GenPassStates.waiting_for_len)
async def process_ip(message: types.Message, state: FSMContext):
    length = message.text

    try:
        length_int = int(length)

        chars = string.ascii_letters + string.digits
        password = ''.join(random.choice(chars) for _ in range(int(length_int)))

        await message.answer(f"Вот ваш пароль: `{password}`", parse_mode="Markdown")

        await state.clear()
    except ValueError:
        await message.answer("Ошибка! Длина должна быть числом! Попробуйте ещё раз")
        return   

# Обработка кнопки "Статистика"
@router.callback_query(F.data == "cmd_stats")
async def stat_handler(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id == ADMIN_ID:
        await callback.message.answer("Статистика: Сервер работает нормально! 📈")
    else:
        await callback.message.answer("Тебе сюда нельзя.")

@router.message(Command("add"))
async def add_server_handler(message: types.Message):
    # 1. Парсим текст сообщения
    # Ожидаем формат: /add 10.0.0.55 MyServer
    try:
        # split() разобьет строку по пробелам.
        # cmd = "/add", ip = "...", hostname = "..."
        cmd, ip, hostname = message.text.split()
    except ValueError:
        await message.answer("❌ Неверный формат!\nПиши так: `/add 10.0.0.1 ServerName`")
        return

    # 2. Готовим данные для API (JSON)
    # Эти поля должны совпадать с твоей Pydantic-схемой ServerCreate в API!
    # CPU и RAM пока зашьем жестко (для простоты), или можно тоже парсить
    server_data = {
        "ip": ip,
        "hostname": hostname,
        "cpu_cores": 2,  # Заглушка
        "ram_gb": 4      # Заглушка
    }

    # 3. Отправляем запрос (Магия aiohttp)
    async with aiohttp.ClientSession() as session:
        try:
            # url должен совпадать с твоим API!
            url = "http://127.0.0.1:8000/create_server"
            
            async with session.post(url, json=server_data) as response:
                # 4. Проверяем ответ сервера
                if response.status == 200:
                    # Успех!
                    result = await response.json() # Если API что-то вернуло
                    await message.answer(f"✅ Сервер **{hostname}** ({ip}) успешно добавлен в Базу Данных!")
                else:
                    # Ошибка (например, 400 - такой IP уже есть)
                    error_text = await response.text()
                    await message.answer(f"⚠️ Ошибка API ({response.status}):\n{error_text}")

        except Exception as e:
            # Если API выключен или нет сети
            await message.answer(f"⛔ Не удалось соединиться с API:\n{e}")

# Обработка кнопки "Поддержка"
@router.callback_query(F.data == "cmd_support")
async def support_handler(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Пиши сюда: @v1ad_shi1ov")

# Обработка кнопки "Пинг"
@router.callback_query(F.data == "cmd_ping")
async def start_ping(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите IP-адрес для проверки:", reply_markup=ping_menu)
    # ПЕРЕКЛЮЧАЕМ ТУМБЛЕР! Бот теперь ждет IP
    await state.set_state(PingStates.waiting_for_ip)

# Отмена действия
@router.callback_query(F.data == "cmd_cancel")
async def support_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    current_state = await state.get_state()
    if current_state is None:
        await callback.message.answer("Нечего отменять")
        return
    
    await state.clear()
    await callback.message.answer("❌ Действие отменено. Вы вернулись в меню", reply_markup=main_menu)

# Обработка IP
@router.message(PingStates.waiting_for_ip)
async def process_ip(message: types.Message, state: FSMContext):
    ip = message.text
    try:
        ip = ipaddress.ip_address(ip)
        await message.answer(f"Пингую {ip}...")
        is_online = await real_ping(message.text)
        if is_online:
            await message.answer(f"✅ {ip} пингуется")
        else:
            await message.answer(f"⚠️ {ip} не отвечает")
        # СБРАСЫВАЕМ СОСТОЯНИЕ (Возвращаем бота в обычный режим)
        await state.clear()
    except ValueError:
        await message.answer(f"❌ Это не похоже на IP-адрес. Попробуй еще раз (например, 8.8.8.8)")

# Ловим "потерянные" нажатия кнопок (на всякий случай)
@router.callback_query()
async def missed_callback_handler(callback: CallbackQuery):
    await callback.answer()
    # Логика для админа/Насти, если они нажали какую-то левую кнопку

# Эхо-хэндлер (Ловит всё остальное, что не попало в фильтры выше)
@router.message()
async def echo_handler(message: types.Message):
    # Асинхронно отправляем ответ
    username = message.from_user.username
    # if message.from_user.id == ADMIN_ID:
    await message.answer(f"Добро пожаловать, {message.from_user.full_name}!")
    await message.answer(f"Выбери действие:", reply_markup=main_menu)
    if username == "NastyaSmolentseva":
        await message.answer(f"Ты ж моё солнышко❤️❤️❤️")
    # else:
        # await message.answer(f"Тебе сюда нельзя")
