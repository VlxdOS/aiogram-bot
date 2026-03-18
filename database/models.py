from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from database.core import Base

class Server(Base):
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column(String(50), unique=True) # IP должен быть уникальным
    name: Mapped[str] = mapped_column(String(100), nullable=True) # Имя сервера (опционально)