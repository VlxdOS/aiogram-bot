# database/requests.py
from database.core import async_session_maker
from database.models import Server
from sqlalchemy import select, delete

async def get_servers():
    async with async_session_maker() as session:
        # Создаем запрос: "Выбрать всё из таблицы Server"
        stmt = select(Server)
        # Выполняем
        result = await session.execute(stmt)
        # scalars().all() превращает результат в чистый список объектов
        return result.scalars().all()
    
async def delete_server(ip: str):
    """Удаляет сервер по IP"""
    async with async_session_maker() as session:
        # Удаляем строки, где ip равен переданному
        stmt = delete(Server).where(Server.ip == ip)
        await session.execute(stmt)
        await session.commit()