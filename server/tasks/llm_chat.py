from llama_index.llms.openai_like import OpenAILike
from llama_index.core.base.llms.types import ChatMessage, MessageRole
import os
import openai

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


def convert_1d_to_2d(lst, extract_field=None, step=2):  
    """  
    将一维列表转换为二维列表。
      
    :param lst: 输入的一维列表  
    :param extract_field: 要提取的字段  
    :param step: 每次从原列表中取出的元素数量，默认为2  
    :return: 转换后的二维列表  
    """  
    if len(lst) % step != 0:  
        raise ValueError("列表长度不是step的整数倍")  
      
    # 使用列表推导式和range的步长来实现
    def one_to_step_d(_lst, _step):
        return [_lst[i:i+_step] for i in range(0, len(_lst), _step)]
    
    result = one_to_step_d(lst, step)  

    if extract_field:
        field_list_one_d = [getattr(obj, extract_field, None) for sublist in result for obj in sublist]
        return one_to_step_d(field_list_one_d, step)
        
    return result

class Chat():
    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id
        self.chat_store = ChatStore(user_id=self.user_id)

    def test_chat(self, query):
        return llm.chat(messages=[ChatMessage(role="user", content=query)])

    async def astream_chat(self, query: str):
        msg_list = self.chat_store.get_chat_history()
        msg_list.append(ChatMessage(role="user", content=query))
        if len(msg_list) > 5:
            msg_list = msg_list[-5: ]

        response = await llm.astream_chat(msg_list)
        async for chunk in response:
            print(chunk.delta, end="")
            yield chunk.delta

    def get_all_chat_history(self, need_raw_str=False):
        # print(f"当前存储路径：{self.chat_store.path}")
        msg_list = self.chat_store.get_chat_history()
        # 如果不需要字符串格式的数据，就返回 List[ChatMessage]，否则构造二维字符串列表
        if not need_raw_str:
            return msg_list
        
        if msg_list and len(msg_list) > 0:
            msg_list2 = convert_1d_to_2d(lst=msg_list, extract_field="content")
            return msg_list2
        
    def save_this_round_msg(self, query, ai_resp):
        msg_in_this_round = [ChatMessage(role=MessageRole.USER, content=query),
                             ChatMessage(role=MessageRole.ASSISTANT, content=ai_resp)]
        self.chat_store.save_messages(msg_in_this_round)

    def test_stream_chat(self, query: str):
        msg_list = [ChatMessage(role="user", content=query)]
        response = llm.stream_chat(msg_list)
        for chunk in response:
            print(chunk.delta, end="")


if __name__ == "__main__":
    c = Chat(user_id="32906025200850466097890969438382775665167326886116576518565743686775373059432")
    his = c.get_all_chat_history()
    print(his)