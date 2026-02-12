import ipaddress
import asyncio
import platform

from aiogram import types, F, Router
from aiogram.filters.command import Command
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID

from keyboards import main_menu
from keyboards import ping_menu

router = Router()

class PingStates(StatesGroup):
    waiting_for_ip = State()

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
# Команда /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID or message.from_user.username == "NastyaSmolentseva":
        await message.answer("Привет, Админ!", reply_markup=main_menu)
    else:
        await message.answer("Привет, юзер!")

# Обработка кнопки "Статистика"
@router.callback_query(F.data == "cmd_stats")
async def stat_handler(callback: CallbackQuery):
    await callback.answer()
    if callback.from_user.id == ADMIN_ID:
        await callback.message.answer("Статистика: Сервер работает нормально! 📈")
    else:
        await callback.message.answer("Тебе сюда нельзя.")

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
