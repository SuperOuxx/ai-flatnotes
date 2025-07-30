import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件所在目录
CHAT_STORE_PATH = os.path.join(BASE_DIR, "local_chat_store/[user_id].json")