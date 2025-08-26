
from typing import Literal
import uuid
from helpers import CustomBaseModel


class TaskCreate(CustomBaseModel):
    query: str = ""
    simple_chat: int = 1
    chat_with_notes: int = 0
    chat_with_knowledge: int = 0
    chat_with_web: int = 0

class TaskResult(CustomBaseModel):
    task_id: str = ""
    user_id: int
    status: Literal["pending", "completed"] = "pending" # 任务状态，待办、完成
    result: str = ""

from sqlalchemy import Column, BigInteger, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy.orm import mapped_column

def convert_val(value):
    if isinstance(value, str) and len(value.strip()) > 0:
        if str.isdigit(value):
            value = int(value)
    return value

class Base(DeclarativeBase):
    id = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __init__(self, dictionary):
        super().__init__()
        
        for key, value in dictionary.items():
            self.update_value(key, value)

    def update_value(self, key, value):
        # if value and key in self.__dict__.keys():
        setattr(self, key, convert_val(value))

class ChatSession(Base):
    __tablename__ = 'chat_session'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    
    title = Column(String, nullable=True)  # 会话标题
    summarize = Column(String, nullable=True)  # 会话总结，用于给上下游信息


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = f"""postgresql://postgres:{os.environ.get("FLATNOTES_PASSWORD")}@127.0.0.1:5432/postgres"""