from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.vector_stores.elasticsearch import ElasticsearchStore, AsyncSparseVectorStrategy


class KnowledgeGraph:

    def __init__(self):
        # 默认是稠密的
        self.vector_store = ElasticsearchStore(
            index_name="my_index",
            es_url="http://localhost:9200",
        )

        # 稀疏
        self.sparse_vector_store = ElasticsearchStore(
            es_url="http://localhost:9200",  # for Elastic Cloud authentication see above
            index_name="movies_dense",
            retrieval_strategy=AsyncSparseVectorStrategy(model_id=".elser_model_2"),
        )

    def print_results(self, results):
        for rank, result in enumerate(results, 1):
            print(
                f"{rank}. title={result.metadata['title']} score={result.get_score()} text={result.get_text()}"
            )


    def search(self,
        vector_store: ElasticsearchStore, nodes: list[TextNode], query: str
    ):
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(nodes, storage_context=storage_context)

        print(">>> Documents:")
        retriever = index.as_retriever()
        results = retriever.retrieve(query)
        self.print_results(results)

        print("\n>>> Answer:")
        query_engine = index.as_query_engine()
        response = query_engine.query(query)
        print(response)

    def sparse_search(self, nodes: list[TextNode], query: str):
        return self.search(self.sparse_vector_store, nodes, query)