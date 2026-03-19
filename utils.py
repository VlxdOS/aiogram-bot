import asyncio
import platform
import random
import string

import psutil

async def ping_ip(ip: str) -> bool:
    """
    Пингует IP и возвращает True, если хост доступен, иначе False.
    Работает асинхронно, не блокируя бота.
    """
    # Определяем параметр количества пакетов: -n для Windows, -c для Linux/Mac
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    try:
        process = await asyncio.create_subprocess_shell(
            f"ping {param} 1 {ip}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await process.wait()
        return process.returncode == 0
    except Exception:
        return False
    
def generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choice(chars) for _ in range(length))

def get_system_load():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Преобразуем байты в гигабайты
    ram_used = round(ram.used / (1024**3), 1)
    ram_total = round(ram.total / (1024**3), 1)
    disk_free = round(disk.free / (1024**3), 1)
    
    return f"🔥 CPU: {cpu}%\n💾 RAM: {ram_used}/{ram_total} GB\n💿 Disk Free: {disk_free} GB"