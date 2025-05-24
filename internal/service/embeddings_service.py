import os
from dataclasses import dataclass
from typing import List
import tiktoken
from injector import inject
from langchain.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

# from langchain_huggingface import HuggingFaceEmbeddings
from redis import Redis

from langchain_community.embeddings import QianfanEmbeddingsEndpoint

ak = "uexDJXSAF3qDg7tR3vkQZLOS"
sk = "ovpeF9z5CcZleDczaFuc49AVhOjxGezS"


class QianfanFloatEmbedding(Embeddings):
    """包装 QianfanEmbeddingsEndpoint 以确保输出为 float 类型。"""

    def __init__(self, **kwargs):
        # 初始化原始的 Qianfan Embedding 实例
        self.qianfan_embedding = QianfanEmbeddingsEndpoint(**kwargs)

    def embed_documents(self, texts: List[str]):
        """嵌入文档列表。"""
        # 调用原始 embedding 方法获取向量
        embeddings = self.qianfan_embedding.embed_documents(texts)
        # 强制将每个向量中的所有值转换为 float
        return [[float(val) for val in emb] for emb in embeddings]

    def embed_query(self, text: str):
        """嵌入单个查询文本。"""
        # 调用原始 embedding 方法获取向量
        embedding = self.qianfan_embedding.embed_query(text)
        # 强制将向量中的所有值转换为 float
        return [float(val) for val in embedding]


@inject
@dataclass
class EmbeddingsService:
    """文本嵌入模型服务"""

    _store: RedisStore
    _embeddings: Embeddings
    _cache_backed_embeddings: CacheBackedEmbeddings

    def __init__(self, redis: Redis):
        """构造函数，初始化文本嵌入模型客户端、存储器、缓存客户端"""
        self._store = RedisStore(client=redis)
        # self._embeddings = HuggingFaceEmbeddings(
        #     model_name="nomic-ai/nomic-embed-text-v1.5",
        #     cache_folder=os.path.join(os.getcwd(), "internal", "core", "embeddings"),
        #     model_kwargs={
        #         "trust_remote_code": True,
        #     },
        # )
        self._embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
        )
        self._embeddings = QianfanFloatEmbedding(
            qianfan_ak=ak,
            qianfan_sk=sk,
            model="embedding-v1",
        )
        self._cache_backed_embeddings = CacheBackedEmbeddings.from_bytes_store(
            self._embeddings,
            self._store,
            namespace="embeddings",
        )

    @classmethod
    def calculate_token_count(cls, query: str) -> int:
        """计算传入文本的token数"""
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(query))

    @property
    def store(self) -> RedisStore:
        return self._store

    @property
    def embeddings(self) -> Embeddings:
        return self._embeddings

    @property
    def cache_backed_embeddings(self) -> CacheBackedEmbeddings:
        return self._cache_backed_embeddings
