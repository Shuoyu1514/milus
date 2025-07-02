import uuid
import requests
from typing import List
from pymilvus import MilvusClient, DataType

class EmbeddingClient:
    def __init__(self, api_key: str, url: str):
        self.api_key = api_key
        self.url = url

    def get_embedding(self, texts: List[str]) -> List[List[float]]:
        headers = {
            "BCS-APIHub-RequestId": str(uuid.uuid4()),
            "X-CHJ-GWToken": self.api_key,
            "Content-Type": "application/json"
        }
        data = {"input": texts}
        response = requests.post(self.url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        # print("API 返回内容：", result)
        return [item["embedding"] for item in result["data"]]

if __name__ == "__main__":
    # 配置
    TOKEN = "..."
    URL = "..."
    COLLECTION_NAME = "demo_embedding"

    # 1. 获取 embedding
    client = EmbeddingClient(api_key=TOKEN, url=URL)
    texts = ["你好，世界", "人工智能是1956年作为学科成立的。", "图灵是AI领域的先驱。"]
    embeddings = client.get_embedding(texts)
    # print("Embedding 维度:", len(embeddings[0]))

    # 2. 连接 Milvus，连接本地或容器中的 Milvus 服务。
    milvus = MilvusClient(uri="http://localhost:19530")

    # 3. 创建 Collection（如果存在则先删除）
    if milvus.has_collection(COLLECTION_NAME):
        milvus.drop_collection(COLLECTION_NAME)
        print(f"已删除已存在的 Collection: {COLLECTION_NAME}")

    # 3.1 使用 MilvusClient 的辅助函数来定义 Schema
    schema = milvus.create_schema(
        auto_id=True,
        enable_dynamic_field=False,
    )

    # 3.2 为 Schema 添加字段 (*** 这里是关键修正 ***)
    # 使用 DataType.INT64, DataType.FLOAT_VECTOR, DataType.VARCHAR
    # schema（模式）指的是“表结构”或“集合结构”的定义，也就是你要存储的数据的字段、类型、主键等的描述。
    schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
    schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=len(embeddings[0]))
    schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=512)

    # 3.3 定义索引参数
    index_params = milvus.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="AUTOINDEX",
        metric_type="L2"
    )

    # 3.4 使用定义好的 Schema 和索引来创建 Collection
    print(f"正在创建 Collection: {COLLECTION_NAME}...")
    milvus.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
        index_params=index_params
    )
    print("Collection 创建成功！")

    # 4. 插入数据
    print("正在插入数据...")
    data = [
        {"vector": embeddings[i], "text": texts[i]} for i in range(len(texts))
    ]
    milvus.insert(collection_name=COLLECTION_NAME, data=data)
    print("数据插入成功！")
    
    # 5. 检索
    print("正在检索...")
    query_text = "世界"
    query_embedding = client.get_embedding([query_text])[0]
    res = milvus.search(
        collection_name=COLLECTION_NAME,
        data=[query_embedding],
        limit=3,
        output_fields=["text"]
    )
    print("检索结果：")
    for hit in res[0]:
        print(f"text: {hit['entity']['text']}, score: {hit['distance']}")