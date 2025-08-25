from typing import Dict, List
import requests
import json


def network_retrieval_bocha(query):
    """
    联网搜索，返回AI搜索结果列表。
    :param query: str,
    :return: List[dict],
    """
    url = "https://api.bochaai.com/v1/ai-search"
    payload = json.dumps({
        "query": f"{query}",
        "freshness": "oneYear",
        "count": 50,
        "answer": False,
        "stream": False,
    })
    headers = {
        'Authorization': 'sk-5caab5d8495f4ac08e5eda4e34802816',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive',
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    txt = response.json()
    res = json.loads(txt['messages'][0]['content'])['value']
    return res


##
def rerank_bocha(query, documents: list):
    """
        语义重排序，返回Top-N排序索引与分数。
        :param query: str,
        :param documents: List[str],
        :return: List[tuple],
        """
    url = "https://api.bochaai.com/v1/rerank"
    payload = json.dumps({
        "model": "gte-rerank",
        "query": query,
        "documents": documents,
        "return_documents": True,
    })
    headers = {
        'Authorization': 'sk-5caab5d8495f4ac08e5eda4e34802816',
        'Content-Type': 'application/json',
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    if response and response.status_code == 200 and 'data' in response.json():
        return [(info['index'], info['relevance_score']) for info in response.json()['data']['results']]
    else:
        return []


def rerank(query, documents: List[str], web_pages: List[Dict]):
    """
    语义重排序，返回Top-N排序索引与分数。
    :param query: str,
    :param documents: List[str], web_pages 中的 summary
    :param exist_corpus: List[str], 从知识库检索到的语料
    :param web_pages: List[Dict], 从网络（如腾讯）检索到的网页
    :return: List[tuple],
    """
    ranked_pages = rerank_bocha(query, documents)
    show_pages = []
    for index, score in ranked_pages:
        if score < 0.4:
            break
        show_pages.append(web_pages[index])
    return show_pages