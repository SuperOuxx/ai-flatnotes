import requests
import json


def search_tavily(query, max_results=5):
    """
    联网搜索，返回AI搜索结果列表。
    :param query: str,
    :return: List[dict],
    """
    url = "https://api.tavily.com/search"
    payload = json.dumps({
        "query": f"{query}",
        "topic": "general",
        "search_depth": "advanced",
        "chunks_per_source": 3,
        "max_results": max_results,
        "time_range": None,
        "days": 7,
        "include_answer": True,
        "include_raw_content": True,
        "include_images": False,
        "include_image_descriptions": False,
        "include_domains": [],
        "exclude_domains": [],
    })
    headers = {
        'Authorization': '',
        'Content-Type': 'application/json',
        'Connection': 'keep-alive',
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    results = response.json()
    resp_list = []
    id = 0
    if 'results' in results:
        for result in results['results']:
            id += 1
            resp_list.append(
                    {
                    "id": result.get("id", id),
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "summary": result.get("content", ""),  # content
                    "detail": result.get("raw_content", ""),
                    "score": result.get("score", 0)
                    }
                )
            
        resp_list.sort(key=lambda item: item.get("score"), reverse=True)
    return resp_list

