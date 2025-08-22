from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core import (
    StorageContext, 
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    PromptTemplate
    )

from rag.embed import BgeM3SparseEmbeddingFunction
from helpers import get_env


class HybridSearch:
    def __init__(self):
        self.vector_store = MilvusVectorStore(
            uri=get_env("MILVUS_URI"),
            token=get_env("MILVUS_TOKEN"),
            dim=1536,
            enable_sparse=True,
            sparse_embedding_function=BgeM3SparseEmbeddingFunction(),
            overwrite=True,
        )

        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

        self.kb_file_path = get_env("KB_FILE_PATH")

    def load_kb_docs(self):
        # Load documents
        loader = SimpleDirectoryReader(
            input_dir=self.kb_file_path, required_exts=[".md", ".pdf"], recursive=True
        )
        return loader.load_data()

    def set_index_from_docs(self, documents):
        self.index = VectorStoreIndex.from_documents(
            documents, storage_context=self.storage_context
        )

    async def aquery(self, query: str):
        docs = self.load_kb_docs()
        self.set_index_from_docs(docs)

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

        self.query_engine = self.index.as_query_engine(streaming=True,
            vector_store_query_mode="hybrid", similarity_top_k=5
        )
        self.query_engine.update_prompts(
            {"response_synthesizer:text_qa_template": qa_prompt_tmpl}
        )

        return self.query_engine.aquery(query)
        # 调用方 这样用：
            # for chunk in streaming_response.response_gen:
            #     answer += chunk