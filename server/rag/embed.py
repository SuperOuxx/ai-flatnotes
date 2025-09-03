from FlagEmbedding import BGEM3FlagModel
from typing import List
from llama_index.vector_stores.milvus.utils import BaseSparseEmbeddingFunction

from helpers import get_env


class BgeM3SparseEmbeddingFunction(BaseSparseEmbeddingFunction):
    def __init__(self):
        self.model = BGEM3FlagModel(model_name_or_path=get_env("EMBEDDING_MODEL_PATH"), use_fp16=False)

    def encode_queries(self, queries: List[str]):
        outputs = self.model.encode(
            queries,
            return_dense=False,
            return_sparse=True,
            return_colbert_vecs=False,
        )["lexical_weights"]
        return [self._to_standard_dict(output) for output in outputs]

    def encode_documents(self, documents: List[str]):
        outputs = self.model.encode(
            documents,
            return_dense=False,
            return_sparse=True,
            return_colbert_vecs=False,
        )["lexical_weights"]
        return [self._to_standard_dict(output) for output in outputs]

    def _to_standard_dict(self, raw_output):
        result = {}
        for k in raw_output:
            result[int(k)] = raw_output[k]
        return result
    
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
# pip install sentence-transformers[onnx]

# loads BAAI/bge-small-en-v1.5 with the onnx backend
embed_model = HuggingFaceEmbedding(
    model_name=get_env("EMBEDDING_MODEL_PATH"),
    device="cpu",
    # model_kwargs={
    #     "provider": "CPUExecutionProvider"
    # },  # For ONNX, you can specify the provider, see https://sbert.net/docs/sentence_transformer/usage/efficiency.html
)

Settings.embed_model = embed_model