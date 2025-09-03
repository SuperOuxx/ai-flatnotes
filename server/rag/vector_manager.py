from llama_index.vector_stores.milvus import MilvusVectorStore
from pymilvus import MilvusClient

from helpers import get_env

# 2. Milvus向量存储管理
class MilvusManager:
    def __init__(
        self, 
        collection_name: str = "notes_kb",
        embed_dim: int = 1536
    ):
        self.collection_name = collection_name
        self.embed_dim = embed_dim
        self.vector_store = None

        
    def _check_collection_exists(self) -> bool:
        """检查集合是否存在"""
        try:
            return pymilvus.utility.has_collection(self.collection_name, using="default")
        except Exception:
            return False
    
    def create_collection(self):
        """创建新的集合"""
        try:
            # 如果集合已存在则删除（仅用于开发环境）
            if pymilvus.utility.has_collection(self.collection_name):
                pymilvus.utility.drop_collection(self.collection_name)
                print(f"♻️ 已删除现有集合: {self.collection_name}")
            
            # 定义集合Schema
            fields = [
                pymilvus.FieldSchema(
                    name="id", 
                    dtype=pymilvus.DataType.INT64, 
                    is_primary=True, 
                    auto_id=True
                ),
                pymilvus.FieldSchema(
                    name="embedding", 
                    dtype=pymilvus.DataType.FLOAT_VECTOR, 
                    dim=self.embed_dim
                ),
                pymilvus.FieldSchema(
                    name="text",
                    dtype=pymilvus.DataType.VARCHAR,
                    max_length=65535
                ),
                pymilvus.FieldSchema(
                    name="source",
                    dtype=pymilvus.DataType.VARCHAR,
                    max_length=255
                ),
                pymilvus.FieldSchema(
                    name="chunk_id",
                    dtype=pymilvus.DataType.VARCHAR,
                    max_length=255
                ),
                pymilvus.FieldSchema(
                    name="page",
                    dtype=pymilvus.DataType.INT64
                )
            ]
            
            # 创建集合
            schema = pymilvus.CollectionSchema(fields)
            collection = pymilvus.Collection(
                name=self.collection_name, 
                schema=schema,
                using="default"
            )
            
            # 创建索引
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index(
                field_name="embedding", 
                index_params=index_params
            )
            
            print(f"✅ 已创建新集合: {self.collection_name}")
            return True
        except Exception as e:
            print(f"❌ 集合创建失败: {e}")
            return False
    
    def get_vector_store(self) -> MilvusVectorStore:
        """获取向量存储实例"""
        if not self._check_collection_exists():
            self.create_collection()
        
        return self.vector_store