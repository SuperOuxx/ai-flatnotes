
from typing import Literal
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