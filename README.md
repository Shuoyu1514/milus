# Milvus 快速入门及面试笔记

## 为什么必须启动三种服务？

- milvus-standalone: 负责理解你的指令（“我要插入向量”、“我要搜索最相似的向量”），执行计算密集型的任务（比如建立索引、进行搜索），并指挥其他两个组件。

- MinIO: 是一个对象存储服务，专门用来存放海量的、非结构化的“大文件”。在 Milvus 里，它负责存储所有原始的向量数据、索引文件等。

- etcd: 是一个高可靠的键值存储数据库。它不存储庞大的向量数据本身，而是存储所有关于这些数据的元数据（Metadata），也就是“描述数据的数据”

## 集合（Collection）的定义和状态。

每个向量文件（在 MinIO 中）存储了哪些 ID 的向量。

系统各组件的健康状态等关键的小信息。

## Docker创建milvus实例

创建数据存储目录
<pre>
cd D:\wangshuoyu\Desktop\milus
New-Item -ItemType Directory -Force -Path ".\volumes\etcd"
New-Item -ItemType Directory -Force -Path ".\volumes\minio"
New-Item -ItemType Directory -Force -Path ".\volumes\milvus"
</pre>

创建 Milvus Pod:
<pre>
podman pod create --name milvus-pod -p 19530:19530 -p 9091:9091
</pre>

在 Pod 内启动 etcd 容器:
<pre>
podman run -d --pod milvus-pod --name milvus-etcd -v D:\wangshuoyu\Desktop\milus\volumes\etcd:/etcd:Z quay.io/coreos/etcd:v3.5.14 etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
</pre>

在 Pod 内启动 MinIO 容器
<pre>
podman run -d --pod milvus-pod --name milvus-minio -e "MINIO_ACCESS_KEY=minioadmin" -e "MINIO_SECRET_KEY=minioadmin" -v D:\wangshuoyu\Desktop\milus\volumes\minio:/minio_data:Z quay.io/minio/minio:RELEASE.2024-06-22T05-26-45Z minio server /minio_data
</pre>

在 Pod 内启动 Milvus Standalone 主服务
<pre>
podman run -d --pod milvus-pod --name milvus-standalone -e "ETCD_ENDPOINTS=localhost:2379" -e "MINIO_ADDRESS=localhost:9000" -v D:\wangshuoyu\Desktop\milus\volumes\milvus:/var/lib/milvus:Z milvusdb/milvus:v2.4.9 milvus run standalone
</pre>

