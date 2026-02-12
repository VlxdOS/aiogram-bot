import ipaddress
import asyncio
import logging
import platform
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import BOT_TOKEN, ADMIN_ID

# Включаем логирование (чтобы видеть в консоли, что происходит)
logging.basicConfig(level=logging.INFO)

# 1. Создаем объект бота
bot = Bot(token=BOT_TOKEN)
# 2. Создаем диспетчер (мозг)
dp = Dispatcher()

# Кнопки
btn_stat = KeyboardButton(text="📊 Статистика")
btn_support = KeyboardButton(text="🆘 Поддержка")
btn_ping = KeyboardButton(text="🌐 Пинг")

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [btn_stat, btn_support], # Первый ряд (две кнопки вместе)
        [btn_ping] 
    ],
    resize_keyboard=True
)

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
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Привет, Админ!", reply_markup=main_menu)
    else:
        await message.answer("Привет, юзер!")

# Обработка кнопки "Статистика"
@dp.message(F.text == "📊 Статистика")
async def stat_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Статистика: Сервер работает нормально! 📈")
    else:
        await message.answer("Тебе сюда нельзя.")

# Обработка кнопки "Поддержка"
@dp.message(F.text == "🆘 Поддержка")
async def support_handler(message: types.Message):
    await message.answer("Пиши сюда: @v1ad_shi1ov")

# Обработка кнопки "Пинг"
@dp.message(F.text == "🌐 Пинг")
async def start_ping(message: types.Message, state: FSMContext):
    await message.answer("Введите IP-адрес для проверки:")
    # ПЕРЕКЛЮЧАЕМ ТУМБЛЕР! Бот теперь ждет IP
    await state.set_state(PingStates.waiting_for_ip)

# Обработка IP
@dp.message(PingStates.waiting_for_ip)
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

# Эхо-хэндлер (Ловит всё остальное, что не попало в фильтры выше)
@dp.message()
async def echo_handler(message: types.Message):
    # Асинхронно отправляем ответ
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"Добро пожаловать, Повелитель!")
        await message.answer(f"Выбери действие:", reply_markup=main_menu)
    elif message.from_user.username == "NastyaSmolentseva":
        await message.answer(f"Ты ж моё солнышко❤️❤️❤️")
    else:
        await message.answer(f"Ты не проходишь фейсконтроль")
        # await message.answer(f"Твой ID: {message.from_user.id}\nТы написал: {message.text}")

# --- ЗАПУСК ---
async def main():
    print("Бот запускается...")
    # Удаляем вебхуки (на всякий случай, чтобы не было конфликтов)
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем бесконечный опрос серверов Telegram
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())