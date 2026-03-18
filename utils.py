import asyncio
import platform
import subprocess

async def ping_ip(ip: str) -> bool:
    """
    Пингует IP и возвращает True, если хост доступен, иначе False.
    Работает асинхронно, не блокируя бота.
    """
    # Определяем параметр количества пакетов: -n для Windows, -c для Linux/Mac
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    # Формируем команду
    command = f"ping {param} 1 {ip}"

    # Запускаем процесс
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    
    # Ждем завершения
    await process.wait()
    
    # returncode == 0 означает успех
    return process.returncode == 0