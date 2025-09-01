from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core import (
    StorageContext, 
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    PromptTemplate
    )

from llama_index.core.vector_stores.types import VectorStoreQueryMode
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

        self.kb_file_path = get_env("FLATNOTES_KB_PATH")
        self.set_vect_index()

    def load_kb_docs(self):
        # Load documents
        loader = SimpleDirectoryReader(
            input_dir=self.kb_file_path, required_exts=[".md", ".pdf"], recursive=True
        )
        return loader.load_data()

    def set_files_index(self, documents):
        self.files_index = VectorStoreIndex.from_documents(
            documents, 
            # storage_context=self.storage_context
        )

    def set_vect_index(self):
        self.vector_index = VectorStoreIndex.from_vector_store(vector_store=self.vector_store)

    async def aquery(self, query: str, from_files: bool=True):
        if from_files:
            docs = self.load_kb_docs()
            self.set_files_index(docs)
            query_engine = self.files_index.as_query_engine(streaming=True,
                vector_store_query_mode=VectorStoreQueryMode.MMR, similarity_top_k=5
            )
        else:
            query_engine = self.vector_index.as_query_engine(streaming=True,
                vector_store_query_mode=VectorStoreQueryMode.HYBRID, similarity_top_k=5
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

        response = await query_engine.aquery(query)
        return response