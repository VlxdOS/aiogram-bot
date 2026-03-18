from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Важно: используем драйвер sqlite+aiosqlite
DATABASE_URL = "sqlite+aiosqlite:///./bot.db"

engine = create_async_engine(DATABASE_URL, echo=True) # echo=True покажет SQL-запросы в консоли

# Фабрика сессий
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Базовый класс для моделей
class Base(DeclarativeBase):
    pass