from llama_index.llms.openai_like import OpenAILike
from llama_index.core.base.llms.types import ChatMessage, MessageRole, CompletionResponse
from llama_index.core import Settings
import os
import requests
import json

from rag.hybrid_search import HybridSearch
from utils.extract_words import choose_longest_word, extract_all_words
from tasks.chat_store import ChatStore
# from chat_store import ChatStore

API_BASE = os.environ.get("OPENAI_API_BASE")
API_KEY = os.environ.get("OPENAI_API_KEY")

Settings.llm = OpenAILike(
    model="ds-r1",
    api_base=API_BASE,
    api_key=API_KEY,
    # context_window=128000,
    is_chat_model=True,
    is_function_calling_model=False,
)

rag = HybridSearch()


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

from sqlalchemy.orm import Session
from .models import ChatSession
from utils.db_util import DbUtils

def llamacpp_restful_req(query: str):
    url = "http://localhost:18080/v1/completions"
    payload = {
        "model": "qwen3",
        "prompt": query
    }

    response = requests.post(url, data=json.dumps(payload))
    resp_json = json.loads(response.text)
    return resp_json["choices"][0]["text"]

# async def llamacpp_restful_req(query: str):
#     local_lm = Ollama(model="qwen3", base_url="http://10.28.6.59:11434", request_timeout=90.0)
#     return await local_lm.acomplete(query) #.complete(query).text

def complete(query: str):
    rst = Settings.llm.complete(prompt=query)
    return rst.text


def extract_keywords(query: str):
    prompt = f"""请从以下[内容]提炼出5个关键词，总输出30个字以内，无需过多解释，只需要输出关键词。\r\n[内容]: {query}\r\n[关键词]: """
    keywords = complete(prompt)
    # return keywords.split("</think>", 1)[-1].strip()
    return " ".join(extract_all_words(keywords.split("</think>", 1)[-1].strip()))

def summary(query: str):
    prompt = f"""请总结以下[内容]，要求20个字以内，简明精炼。\r\n[内容]: {query}\r\n[总结]: """
    keywords = complete(prompt)
    return keywords.split("</think>", 1)[-1].strip()

class Chat():
    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id
        self.chat_store = ChatStore(user_id=self.user_id)
        self.db = DbUtils()


    def get_or_create_session(self, title: str, session_id: str = None) -> ChatSession:
        if session_id:
            session = self.db.get_by(ChatSession, 
                id=session_id,
                user_id=self.user_id
            )
            if session:
                return session[0].id

        # 创建新会话
        new_session = ChatSession({
            "user_id": self.user_id,
            "title": title
        })
        return self.db.save(new_session)


    def get_all_sessions(self):
        return self.db.get_sorted(ChatSession, user_id=self.user_id)

    def update_session_title(self, session_id: str, title: str):
        # self.db.update(ChatSession, {"title": title})
        session = self.db.get_by_id(ChatSession, id=session_id)
        if session:
            session.title = title
            self.db.save(session)
            return True
        return False
    
    def update_session_summarize(self, session_id: str, summarize: str):
        # self.db.update(ChatSession, {"title": title})
        session = self.db.get_by_id(ChatSession, id=session_id)
        if session:
            session.summarize = summarize
            self.db.save(session)
            return True
        return False

    def get_session_summarize(self, session_id: str):
        if session_id:
            session = self.db.get_by_id(ChatSession, id=session_id)
            if session:
                return session.summarize
        return ""
    
    def get_curr_session_id(self):
        return self.curr_session_id
    
    def get_curr_session_title(self):
        return self.curr_session_title
    
    async def stream_chat_session(self, session_id, query: str, need_web: bool=False, need_kb: bool=False):
        title = "New Session"
        if not session_id:
            title = llamacpp_restful_req(f"""请给以下[提问]起一个标题，要求10个字以内，简明精炼，只输出标题。\r\n[提问]: {query}\r\n[标题]: /no_think""")
            title = choose_longest_word(title)
        
        # 获取或创建会话
        self.curr_session_title = title
        self.curr_session_id = self.get_or_create_session(title, session_id)

        return self.astream_chat(self.curr_session_id, query=query, need_web=need_web, need_kb=need_kb)

    async def astream_chat(self, session_id,  query: str, need_web: bool=False, need_kb: bool=False):
        msg_list = self.chat_store.get_chat_history(session_id)
        
        if len(msg_list) > 10:
            msg_list = msg_list[-10: ]

        if need_kb or need_web:
            summarize_keywords = self.get_session_summarize(session_id=session_id)
            if summarize_keywords:
                msg_list.append(ChatMessage(role="user", content=f"[聊天记录关键词]: {summarize_keywords}"))
            response_obj = await rag.aquery(original_query=query, hist_list=msg_list, need_web=need_web, need_kb=need_kb)
            async for chunk in response_obj:
                yield chunk.delta
        else:
            msg_list.append(ChatMessage(role="user", content=query))
            response_obj = await Settings.llm.astream_chat(msg_list)
            async for chunk in response_obj:
                yield chunk.delta

    def get_all_chat_history(self, session_id,  need_raw_str=False):
        # print(f"当前存储路径：{self.chat_store.path}")
        msg_list = self.chat_store.get_chat_history(session_id)
        # 如果不需要字符串格式的数据，就返回 List[ChatMessage]，否则构造二维字符串列表
        if not need_raw_str:
            return msg_list
        
        if msg_list and len(msg_list) > 0:
            msg_list2 = convert_1d_to_2d(lst=msg_list, extract_field="content")
            return msg_list2
        
    def save_this_round_msg(self, query, ai_resp, session_id):
        msg_in_this_round = [ChatMessage(role=MessageRole.USER, content=query),
                             ChatMessage(role=MessageRole.ASSISTANT, content=ai_resp)]
        self.chat_store.save_messages(msg_in_this_round, session_id)
        summarize = extract_keywords(ai_resp.split("</think>", 1)[-1].strip())
        self.update_session_summarize(session_id, summarize)

    def search_sessions(self, term: str):
        """Search sessions by title using PostgreSQL ILIKE for case-insensitive fuzzy matching"""
        
        from sqlalchemy import and_
        # Use SQLAlchemy ORM for PostgreSQL ILIKE query
        return self.db.filter(
            ChatSession,
            ChatSession.user_id == self.user_id,
            ChatSession.title.ilike(f'%{term}%')
        )



# if __name__ == "__main__":
#     c = Chat(user_id="32906025200850466097890969438382775665167326886116576518565743686775373059432")
#     his = c.get_all_chat_history()
#     print(his)