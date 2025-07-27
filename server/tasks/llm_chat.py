from llama_index.llms.openai_like import OpenAILike
from llama_index.core.base.llms.types import ChatMessage
import os

from tasks.chat_store import ChatStore
# from chat_store import ChatStore

API_BASE = os.environ.get("OPENAI_API_BASE")
API_KEY = os.environ.get("OPENAI_API_KEY")

llm = OpenAILike(
    model="ds-r1",
    api_base=API_BASE,
    api_key=API_KEY,
    # context_window=128000,
    is_chat_model=True,
    is_function_calling_model=False,
)

class Chat():
    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id
        self.chat_store = ChatStore(user_id=self.user_id)

    async def astream_chat(self, query: str):
        msg_list = self.chat_store.get_chat_history()
        msg_list.append(ChatMessage(role="user", content=query))
        if len(msg_list) > 5:
            msg_list = msg_list[-5: ]

        response = llm.astream_chat(msg_list)
        async for chunk in response:
            print(chunk.delta, end="")
            yield chunk.delta

    def test_stream_chat(self, query: str):
        msg_list = [ChatMessage(role="user", content=query)]
        response = llm.stream_chat(msg_list)
        for chunk in response:
            print(chunk.delta, end="")


if __name__ == "__main__":
    c = Chat(user_id="1")
    c.test_stream_chat("你是谁")