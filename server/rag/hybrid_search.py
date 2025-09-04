from typing import List
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core.llms import ChatMessage
from llama_index.core import (
    Settings, 
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    PromptTemplate,
    StorageContext
    )
from llama_index.core.schema import Document, TextNode
from llama_index.core.node_parser.file.markdown import MarkdownNodeParser
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pymilvus import DataType, connections, utility
import pymilvus

from rag.embed import BgeM3SparseEmbeddingFunction
from helpers import get_env
from utils.extract_words import extract_first_quoted_string


class HybridSearch:
    def __init__(self):
        self.collection_name = "notes_kb"
        self.embed_dim = 1024 # 1536
        self.min_confidence = 0.6
        self.kb_file_path = get_env("FLATNOTES_KB_PATH")
        self.files_loader = None
        self.files_index = None
        self.vector_index = None

        self.vector_store = None

        for i in range(3):
            if self.vector_store:
                break
            try:
                connections.connect(uri=get_env("MILVUS_URI"), token=get_env("MILVUS_TOKEN"))
                self.vector_store = MilvusVectorStore(
                    uri=get_env("MILVUS_URI"),
                    token=get_env("MILVUS_TOKEN"),
                    dim=self.embed_dim,
                    enable_sparse=True,
                    sparse_embedding_function=BgeM3SparseEmbeddingFunction(),
                    overwrite=False,
                    collection_name=self.collection_name,
                    # scalar_field_names=["source", "chunk_id", "page"],
                    # scalar_field_types=[DataType.VARCHAR, DataType.VARCHAR, DataType.INT64],
                )
                self.client = self.vector_store.client
                # 创建存储上下文
                self.storage_context = StorageContext.from_defaults(
                    vector_store=self.vector_store
                )
            except Exception:
                continue

        if not self.client.has_collection(self.collection_name):
            
            self.client.create_collection(collection_name=self.collection_name, 
                                        #   schema=pymilvus.CollectionSchema(fields=fields)
                                          )
        # TODO 暂时屏蔽
        if self._is_collection_empty():
            documents = self.load_kb_docs()
            self.create_index(documents)


    def _is_collection_empty(self) -> bool:
        """检查集合是否为空"""
        try:
            collection = pymilvus.Collection(
                self.collection_name
            )
            
            collection.load()
            return collection.num_entities == 0
        except Exception as e:
            print(f"⚠️ 集合检查失败: {e}")
            return True
        
    def load_kb_docs(self):
        # Load documents
        if not self.files_loader:
            self.files_loader = SimpleDirectoryReader(
                input_dir=self.kb_file_path, required_exts=[".md", ".pdf"], recursive=True
            )
        return self.files_loader.load_data()

    def set_files_index(self, documents):
        self.files_index = VectorStoreIndex.from_documents(
            documents, 
            # storage_context=self.storage_context
        )


    def create_index(self, documents: List[Document]):
        # self.vector_index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store)

        # 文档分块
        node_parser = MarkdownNodeParser(include_metadata=True, include_prev_next_rel=True)
        nodes = []
        
        for doc in documents:
            doc_nodes = node_parser.get_nodes_from_documents([doc])
            for node in doc_nodes:
                # 添加元数据
                node.metadata = {
                    "source": doc.metadata.get("file_path", "unknown"),
                    "page": doc.metadata.get("page_label", 0),
                    "chunk_id": f"{doc.doc_id}_{len(nodes)}"
                }
            nodes.extend(doc_nodes)
        
        print(f"✂️ 已将文档分成 {len(nodes)} 个文本块")
        
        # 存储到Milvus
        # self.storage_context.vector_store.add(nodes)
        self.vector_index = VectorStoreIndex(
            nodes=nodes, 
            storage_context=self.storage_context
        )
        # self.vector_index.build_index_from_nodes(nodes=nodes)
        print(f"💾 已存储 {len(nodes)} 个文本块到Milvus集合 {self.collection_name}")

    def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        """检索知识库并返回片段"""
        if not self.vector_index:
            self.vector_index = VectorStoreIndex.from_vector_store(self.vector_store)
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
    
    async def aquery(self, original_query: str, hist_list: List[ChatMessage], from_local_files: bool=False,
                     need_web: bool=False, need_kb: bool=False):
        if from_local_files:
            docs = self.load_kb_docs()
            self.set_files_index(docs)
            query_engine = self.files_index.as_query_engine(streaming=True,
                vector_store_query_mode=VectorStoreQueryMode.MMR, similarity_top_k=5
            )
            # Setup streaming query engine with custom prompt
            qa_prompt_tmpl_str = (
                "Context information is below.\n"
                "---------------------\n"
                "{context_str}\n"
                "---------------------\n"
                "Given the context information above I want you to think step by step to answer the query in a crisp manner, incase case you don't know the answer say 'I don't know!'.\n"
                "Query: {query_str}\n"
                "Answer: "
            )
            qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)

            
            query_engine.update_prompts(
                {"response_synthesizer:text_qa_template": qa_prompt_tmpl}
            )

            response = await query_engine.aquery(original_query)
            return response
        else:
            # 如果有历史记录，则根据历史记录重写查询
            refined_query = refine_query_with_context(original_query, hist_list) if hist_list else original_query
            
            # 步骤1: 知识库检索
            knowledge_nodes, kb_qualified_nodes, knowledge_confident = [], [], False
            if need_kb:
                knowledge_nodes = self.retrieve(refined_query)
                # 检查知识库置信度
                kb_qualified_nodes = [node for node in knowledge_nodes if node["score"] >= self.min_confidence]
                knowledge_confident = (len(kb_qualified_nodes) > 1)
            
                # # 步骤2: 重写查询
                # refined_query = refine_query_with_context(original_query, 
                #                                           kb_qualified_nodes if knowledge_confident else knowledge_nodes)
            
            # 步骤3: 决定是否联网检索。知识库置信度低，或提问中出现了“最新”“当前”的关键词，则联网检索
            web_results = []
            if need_web:
                if not knowledge_confident or ("最新" in original_query or "当前" in original_query):
                    web_results = search_web(refined_query)
                else:
                    print("ℹ️ 知识库置信度高，或提问中没有“最新”“当前”的关键词，跳过联网检索")
            
            # 步骤4: 生成最终响应
            return await generate_final_response(
                refined_query, hist_list,
                kb_qualified_nodes if knowledge_confident else knowledge_nodes,
                web_results
            )

import datetime
today = datetime.datetime.today()
curr_year = today.year

# 3. 片段整理与查询重写
def refine_query_with_context(original_query: str, context_nodes: List[dict]) -> str:
    """根据聊天历史重写查询"""
    # 提取关键信息
    context_summary = "\n".join(
        f"[片段{i + 1}] {node.role} : {node.content}"
        for i, node in enumerate(context_nodes[-3:])
    )
    
    # 重写查询的提示词
    prompt = f"""
    [原始查询]:{original_query}
    
    [聊天历史]:
    {context_summary}
    
    请根据以上内容优化原始查询，使其更适合进行联网检索：
    1. 保留核心查询意图
    2. 添加必要的限定词（如判断是时效性高的需求，时间必须为{curr_year}年；专业术语）
    3. 移除已在[聊天历史]中找到的信息
    4. 输出格式：直接返回优化后的查询语句
    """
    
    # 调用LLM重写查询
    refined_query = Settings.llm.complete(prompt).text.split("</think>", 1)[-1].strip()
    
    # 清理输出，确保只返回查询语句
    if "优化后" in refined_query:
        refined_query = extract_first_quoted_string(refined_query.split("优化后的查询")[-1])
    
    print(f"🔄 查询重写结果: {refined_query}")
    print(f"🔄 聊天记录的总结: {context_nodes[-1]}")
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
    return  reranked_results # "\n".join([r.get("summary") for r in reranked_results]), reranked_results


# 5. 响应合成器
async def generate_final_response(
    original_query: str, hist_list: List[ChatMessage], 
    knowledge_nodes: List[dict],
    web_results: List[dict]
):
    """结合知识库和网络结果生成最终响应"""
    # 组织输入内容
    knowledge_content = "\n".join(
        f"【知识库片段 {i+1}】{node['content']}\n(来源: {node['source']}, 置信度: {node['score']:.2f})\n" 
        for i, node in enumerate(knowledge_nodes)
    )
    knowledge_content = f"""### 知识库内容：\n{knowledge_content}""" if knowledge_content else ""
    # "<br>网络检索结果：</br>" + "\r\n".join([f"""<u><font color="orange">[{web["title"]}]({web["url"]})</font></u>""" for web in web_rst])
    
    web_content = "\n".join(
        f"""【网络结果 {i+1}】[{res["title"]}]({res["url"]}))\n""" 
        for i, res in enumerate(web_results)
    )
    web_content = f"""### 网络检索结果：\n{web_content}""" if web_content else ""
    
    # 生成最终响应的提示词
    prompt = f"""
    ## 任务说明
    请基于以下信息回答用户查询：
    
    ### 用户原始查询：
    {original_query}
    
    {knowledge_content}
    
    {web_content}
    
    ## 回答要求：
    1. 如果存在知识库内容，优先使用知识库内容作为主要依据
    2. 网络结果仅用于补充知识库的不足或更新信息
    3. 当内容冲突时，标注来源并说明判断依据
    4. 在回答末尾添加"参考资料"部分，格式：
       - 知识库文档: [文档名称]
       - 网络来源: [标题](链接)
    5. 保持专业且易读的语气
    """

    print(f"generate_final_response Prompt(前200字) = {prompt[:200]}")

    hist_list.append(ChatMessage(role="user", content=prompt))
    
    # 生成最终响应
    response = await Settings.llm.astream_chat(hist_list)
    return response
    # async for chunk in response:
    #     yield chunk.delta