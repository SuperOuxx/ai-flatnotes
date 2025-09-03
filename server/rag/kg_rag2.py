# -*- coding: utf-8 -*-
import os
import re
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from helpers import get_env
import nest_asyncio
from typing import List

# 解决异步IO问题
nest_asyncio.apply()

# 1. 初始化设置
# os.environ["OPENAI_API_KEY"] = "sk-xxxxxxxx"  # 替换为你的OpenAI API Key
# Settings.llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)
# Settings.embed_model = "local:BAAI/bge-small-en-v1.5"

# 2. 知识库检索与片段提取
class KnowledgeBaseRetriever:
    def __init__(self):
        # 加载文档并分块
        documents = SimpleDirectoryReader(get_env("FLATNOTES_KB_PATH")).load_data()
        
        # 创建带有元数据的文本块
        self.nodes = []
        for doc in documents:
            chunks = SentenceSplitter(
                chunk_size=512, 
                chunk_overlap=20
            ).split_text(doc.text)
            
            for i, chunk in enumerate(chunks):
                node = TextNode(
                    text=chunk,
                    metadata={
                        "source": doc.metadata.get("source", "unknown"),
                        "page": doc.metadata.get("page", 0),
                        "chunk_id": f"{doc.doc_id}_{i}"
                    }
                )
                self.nodes.append(node)
        
        # 创建向量索引
        self.vector_index = VectorStoreIndex(self.nodes)
        
    def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        """检索知识库并返回片段"""
        retriever = self.vector_index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        
        # 整理结果片段
        results = []
        for node in nodes:
            source = node.metadata.get("source", "")
            if source.lower().endswith(".pdf"):
                source += f" (Page {node.metadata.get('page', 1)})"
                
            results.append({
                "content": node.text,
                "source": source,
                "score": node.score,
                "chunk_id": node.metadata.get("chunk_id", "")
            })
        
        return results

# 3. 片段整理与查询重写
def refine_query_with_context(original_query: str, context_nodes: List[dict]) -> str:
    """根据知识库片段重写查询"""
    # 提取关键信息
    context_summary = "\n".join(
        f"【片段{i+1}】{node['content'][:200]}..." 
        for i, node in enumerate(context_nodes)
    )
    
    # 重写查询的提示词
    prompt = f"""
    原始查询：{original_query}
    
    相关知识库片段：
    {context_summary}
    
    请根据以上内容优化原始查询，使其更适合进行联网检索：
    1. 保留核心查询意图
    2. 添加必要的限定词（如时间范围、专业术语）
    3. 移除已在知识库中找到的信息
    4. 输出格式：直接返回优化后的查询语句
    """
    
    # 调用LLM重写查询
    refined_query = Settings.llm.complete(prompt).text.split("</think>", 1)[-1].strip()
    
    # 清理输出，确保只返回查询语句
    if "优化后的查询：" in refined_query:
        refined_query = refined_query.split("优化后的查询：")[-1]
    
    print(f"🔄 查询重写结果: {refined_query}")
    return refined_query

# 4. 联网检索工具

from tools.bocha import rerank
from tools.tencent import search_tencent

def search_web(query: str) -> str:
    # keywords = extract_keywords(query)
    # print(f"关键词 = {keywords}")
    tencent_results = search_tencent(query) # search_tencent(keywords + " " + query)
    # tavily_results = search_tavily(query)
    # final_rst = tavily_results + tencent_results
    # documents = [item.get("summary", "") for item in final_rst]
    # reranked_results = rerank(query, documents, final_rst)

    documents = [item.get("summary", "") for item in tencent_results]
    reranked_results = rerank(query, documents, tencent_results)
    return "\n".join([r.get("summary") for r in reranked_results]), reranked_results


# 5. 响应合成器
async def generate_final_response(
    original_query: str, 
    knowledge_nodes: List[dict],
    web_results: List[dict]
):
    """结合知识库和网络结果生成最终响应"""
    # 组织输入内容
    knowledge_content = "\n".join(
        f"【知识库片段 {i+1}】{node['content']}\n(来源: {node['source']}, 置信度: {node['score']:.2f})\n" 
        for i, node in enumerate(knowledge_nodes)
    )
    # "<br>网络检索结果：</br>" + "\r\n".join([f"""<u><font color="orange">[{web["title"]}]({web["url"]})</font></u>""" for web in web_rst])
    
    web_content = "\n".join(
        f"""【网络结果 {i+1}】[{res["title"]}]({res["url"]}))\n""" 
        for i, res in enumerate(web_results)
    )
    
    # 生成最终响应的提示词
    prompt = f"""
    ## 任务说明
    请基于以下信息回答用户查询：
    
    ### 用户原始查询：
    {original_query}
    
    ### 知识库内容：
    {knowledge_content if knowledge_content else "无相关内容"}
    
    ### 网络检索结果：
    {web_content if web_content else "无相关内容"}
    
    ## 回答要求：
    1. 优先使用知识库内容作为主要依据
    2. 网络结果仅用于补充知识库的不足或更新信息
    3. 当内容冲突时，标注来源并说明判断依据
    4. 在回答末尾添加"参考资料"部分，格式：
       - 知识库文档: [文档名称]
       - 网络来源: [标题](链接)
    5. 保持专业且易读的语气
    """
    
    # 生成最终响应
    response = await Settings.llm.astream_chat(prompt)
    async for chunk in response:
        yield chunk.delta

# 6. 主流程控制器
class HybridQueryEngine:
    def __init__(self, data_path="./data"):
        self.retriever = KnowledgeBaseRetriever(data_path)
        self.min_confidence = 0.7  # 知识库置信度阈值
    
    async def aquery(self, original_query: str):
        print(f"\n🔍 知识库检索: {original_query}")
        
        # 步骤1: 知识库检索
        knowledge_nodes = self.retriever.retrieve(original_query)
        
        # 检查知识库置信度
        knowledge_confident = any(node["score"] >= self.min_confidence for node in knowledge_nodes)
        
        # 步骤2: 重写查询
        refined_query = refine_query_with_context(original_query, knowledge_nodes)
        
        # 步骤3: 决定是否联网检索。知识库置信度低，或提问中出现了“最新”“当前”的关键词，则联网检索
        web_results = []
        if not knowledge_confident or "最新" in original_query or "当前" in original_query:
            web_results = search_web(refined_query)
        else:
            print("ℹ️ 知识库置信度高，或提问中没有“最新”“当前”的关键词，跳过联网检索")
        
        # 步骤4: 生成最终响应
        return generate_final_response(
            original_query, 
            knowledge_nodes,
            web_results
        )
        

# 7. 使用示例
if __name__ == "__main__":
    # 初始化引擎
    engine = HybridQueryEngine()
    
    # 测试查询
    queries = [
        "LlamaIndex如何处理大规模数据索引？",
        "当前LlamaIndex的最新版本特性是什么？",
        "如何评估RAG系统的检索质量？"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"📝 用户查询: {query}")
        
        response = engine.aquery(query)
        
        print("\n💡 系统响应:")
        print(response)