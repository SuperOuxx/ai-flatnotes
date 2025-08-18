
from typing import List
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage

from llama_index.storage.chat_store.postgres import PostgresChatStore
import os

from local_path import CHAT_STORE_PATH


# 历史对话的存储路径
# CHAT_STORE_PATH = "./chat_store/[user_id].json"


class LocalChatStore():
    # coder_llm: LLM = Ollama(model=QWEN_2_5_CODER_7B, temperature=0)

    def __init__(self, user_id) -> None:
        self.chat_store = SimpleChatStore()
        self.user_id = user_id
        self.path = CHAT_STORE_PATH.replace("[user_id]", str(user_id))


    def __get_persist_chat_store(self):
        return SimpleChatStore.from_persist_path(
            persist_path=self.path
        )
    
    def get_chat_history(self):
        persist_chat_store = self.__get_persist_chat_store()
        return persist_chat_store.get_messages(key=self.user_id)
    

    def save_messages(self, msg_list: List[ChatMessage]):
        persist_chat_store = self.__get_persist_chat_store()
        for msg in msg_list:
            persist_chat_store.add_message(
                key=self.user_id, message=msg, idx=-1)
            
        persist_chat_store.persist(self.path)


class ChatStore():
    
    def __init__(self, user_id) -> None:
        self.chat_store = PostgresChatStore.from_uri(
            uri=f"""postgresql+asyncpg://postgres:{os.environ.get("FLATNOTES_PASSWORD")}@127.0.0.1:5432/postgres""",
        )
        self.user_id = user_id

    def get_chat_history(self, session_id) -> List[ChatMessage]:
        # VectorStoreIndex.from_vector_store()
        return self.chat_store.get_messages(key = f"{self.user_id}/{session_id}")
    
    def save_messages(self, msg_list: List[ChatMessage], session_id):
        for msg in msg_list:
            self.chat_store.add_message(f"{self.user_id}/{session_id}", message=msg)