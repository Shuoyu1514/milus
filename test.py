import uuid
import requests
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection

# 1. 获取文本的 embedding
def get_embedding(text, token):
    url = "http://api-hub.inner.chj.cloud/llm-gateway/v1/embeddings/azure-text-embedding-ada-002"
    headers = {
        "BCS-APIHub-RequestId": str(uuid.uuid4()),
        "X-CHJ-GWToken": token,
        "Content-Type": "application/json"
    }
    data = {
        "input": [text]
    }
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]

# 2. 连接 Milvus
def connect_milvus():
    connections.connect("default", host="localhost", port="19530")  # 修改为你的 Milvus 地址

# 3. 创建 Collection
def create_collection(collection_name, dim):
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
    ]
    schema = CollectionSchema(fields, description="embedding collection")
    if collection_name in Collection.list_collections():
        Collection(collection_name).drop()
    collection = Collection(collection_name, schema)
    return collection

# 4. 插入数据
def insert_embedding(collection, embedding):
    data = [
        [embedding]  # embedding 列
    ]
    collection.insert([[], embedding])  # auto_id, 只插入向量

# 5. 检索
def search(collection, query_embedding, top_k=3):
    results = collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param={"metric_type": "L2", "params": {"nprobe": 10}},
        limit=top_k,
        output_fields=["id"]
    )
    return results

if __name__ == "__main__":
    # 配置
    TOKEN = "你的token"  # 替换为你的 X-CHJ-GWToken
    COLLECTION_NAME = "demo_embedding"
    DIM = 1024  # 你的 embedding 维度

    # 1. 获取 embedding
    text = "你好，世界"
    embedding = get_embedding(text, TOKEN)
    print("Embedding:", embedding[:5], "...")  # 只打印前5个数

    # 2. 连接 Milvus
    connect_milvus()

    # 3. 创建 Collection
    collection = create_collection(COLLECTION_NAME, len(embedding))

    # 4. 插入数据
    collection.insert([[embedding]])
    collection.flush()

    # 5. 检索
    query_embedding = get_embedding("世界", TOKEN)
    results = search(collection, query_embedding)
    print("Search results:", results) 