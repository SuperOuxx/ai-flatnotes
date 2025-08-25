

# from tasks.llm_chat import extract_keywords
# from tools.bocha import network_retrieval_bocha, rerank
# from tools.tavily import search_tavily
# from tools.tencent import search_tencent

# def search_web(query: str) -> str:
#     keywords = extract_keywords(query)
#     tencent_results = search_tencent(" ".join(keywords) + " " + query)
#     # tavily_results = search_tavily(query)
#     # final_rst = tavily_results + tencent_results
#     # documents = [item.get("summary", "") for item in final_rst]
#     # reranked_results = rerank(query, documents, final_rst)

#     documents = [item.get("summary", "") for item in tencent_results]
#     reranked_results = rerank(query, documents, tencent_results)
#     return "\n".join([r.get("summary") for r in reranked_results]), reranked_results


# def search_web2(query: str) -> str:
#     # 搜索结果列表，初始化为空
#     current_results = []  # 当前步骤的有效结果（每个引擎独立取top2）
#     final_results = []    # 最终用于输出的结果（可能来自任一引擎）
#     max_score: float = 0.0

#     # 1. 优先使用 search_tencent 搜索，并取其top2结果
#     try:
#         tencent_results = search_tencent(query)
#         # 对当前引擎结果单独排序取top2
#         current_results = tencent_results[:2] if len(tencent_results) >= 2 else tencent_results
#         max_score = current_results[0].get("score", 0.0) if current_results else 0
#     except Exception as e:
#         print(f"search_tencent 搜索失败: {str(e)}")
#         current_results = []

#     # 若tencent的top2结果有效（非空且最高分数≥0.6），则加到最终结果
#     if current_results and max_score >= 0.6:
#         final_results.extend(current_results)
#     else:
#         # 2. 否则尝试博查搜索，并取其top2结果
#         try:
#             bocha_results = network_retrieval_bocha(query)
#             current_results = bocha_results[:2] if len(bocha_results) >= 2 else bocha_results
#             max_score = current_results[0].get("score", 0.0) if current_results else 0
#         except Exception as e:
#             print(f"network_retrieval_bocha 搜索失败: {str(e)}")
#             current_results = []

#         # 若博查的top2结果有效，则加到最终结果
#         if current_results and max_score >= 0.6:
#             final_results.extend(current_results)
#         else:
#             # 3. 否则使用 tavily 搜索，并取其top2结果
#             try:
#                 tavily_results = search_tavily(query)
#                 current_results = tavily_results[:2] if len(tavily_results) >= 2 else tavily_results
#                 max_score = current_results[0].get("score", 0.0) if current_results else 0
#             except Exception as e:
#                 print(f"search_tavily 搜索失败: {str(e)}")
#                 current_results = []

#             # 最终使用tavily的top2结果（可能为空）
#             final_results.extend(current_results)

#     # 4. 处理最终结果（仅当最高分数>0.8时重排）
#     if final_results and max_score > 0.8:
#         documents = [item.get("summary", "") for item in final_results]
#         reranked_results = rerank(query, documents, final_results)
#         return " ".join([item.get("summary", "") for item in reranked_results])
#     else:
#         return "未找到足够置信度的搜索结果"
    

# if __name__ == "__main__":
#     rst = search_web("crewAI框架，结合Crew与Flows模式，实现[产品经理crew]与其他crew的协同工作")
#     print(rst)