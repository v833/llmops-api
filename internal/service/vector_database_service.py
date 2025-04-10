
import weaviate
from injector import inject
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_community.embeddings import QianfanEmbeddingsEndpoint
from langchain_weaviate import WeaviateVectorStore
from weaviate import WeaviateClient

ak = 'uexDJXSAF3qDg7tR3vkQZLOS'
sk = 'ovpeF9z5CcZleDczaFuc49AVhOjxGezS'


@inject
class VectorDatabaseService:
    """向量数据库服务"""
    client: WeaviateClient
    vector_store: WeaviateVectorStore

    def __init__(self):
        """构造函数，完成向量数据库服务的客户端+LangChain向量数据库实例的创建"""
        # 1.创建/连接weaviate向量数据库
        self.client = weaviate.connect_to_local()
    
        # 2.创建LangChain向量数据库
        self.vector_store = WeaviateVectorStore(
            client=self.client,
            index_name="Dataset",
            text_key="text",
            embedding=QianfanEmbeddingsEndpoint(
                        qianfan_ak=ak,
                        qianfan_sk=sk,
                        model='embedding-v1',
                )
        )

    def get_retriever(self) -> VectorStoreRetriever:
        """获取检索器"""
        return self.vector_store.as_retriever()

    @classmethod
    def combine_documents(cls, documents: list[Document]) -> str:
        """将对应的文档列表使用换行符进行合并"""
        return "\n\n".join([document.page_content for document in documents])
