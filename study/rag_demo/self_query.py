import dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import QianfanEmbeddingsEndpoint
import os
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings  # Import base class
from typing import List  # For type hinting
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.retrievers import SelfQueryRetriever

key = "pcsk_vTvx6_CQRdW74RPuuRnLfNZeeAFo9Q77SgDLekaUVspFVF1oZFGecPqKm3FoBmzbuZaX2"

dotenv.load_dotenv()


class QianfanFloatEmbedding(Embeddings):
    """包装 QianfanEmbeddingsEndpoint 以确保输出为 float 类型。"""

    def __init__(self, **kwargs):
        # 初始化原始的 Qianfan Embedding 实例
        self.qianfan_embedding = QianfanEmbeddingsEndpoint(**kwargs)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档列表。"""
        # 调用原始 embedding 方法获取向量
        embeddings = self.qianfan_embedding.embed_documents(texts)
        # 强制将每个向量中的所有值转换为 float
        return [[float(val) for val in emb] for emb in embeddings]

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询文本。"""
        # 调用原始 embedding 方法获取向量
        embedding = self.qianfan_embedding.embed_query(text)
        # 强制将向量中的所有值转换为 float
        return [float(val) for val in embedding]


documents = [
    Document(
        page_content="肖申克的救赎",
        metadata={"year": 1994, "rating": 9.7, "director": "弗兰克·德拉邦特"},
    ),
    Document(
        page_content="霸王别姬",
        metadata={"year": 1993, "rating": 9.6, "director": "陈凯歌"},
    ),
    Document(
        page_content="阿甘正传",
        metadata={"year": 1994, "rating": 9.5, "director": "罗伯特·泽米吉斯"},
    ),
    Document(
        page_content="泰坦尼克号",
        metadat={"year": 1997, "rating": 9.5, "director": "詹姆斯·卡梅隆"},
    ),
    Document(
        page_content="千与千寻",
        metadat={"year": 2001, "rating": 9.4, "director": "宫崎骏"},
    ),
    Document(
        page_content="星际穿越",
        metadat={"year": 2014, "rating": 9.4, "director": "克里斯托弗·诺兰"},
    ),
    Document(
        page_content="忠犬八公的故事",
        metadat={"year": 2009, "rating": 9.4, "director": "莱塞·霍尔斯道姆"},
    ),
    Document(
        page_content="三傻大闹宝莱坞",
        metadat={"year": 2009, "rating": 9.2, "director": "拉库马·希拉尼"},
    ),
    Document(
        page_content="疯狂动物城",
        metadat={"year": 2016, "rating": 9.2, "director": "拜伦·霍华德"},
    ),
    Document(
        page_content="无间道",
        metadat={"year": 2002, "rating": 9.3, "director": "刘伟强"},
    ),
]


llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"))


embeddings = QianfanFloatEmbedding(
    qianfan_ak="uexDJXSAF3qDg7tR3vkQZLOS",
    qianfan_sk="ovpeF9z5CcZleDczaFuc49AVhOjxGezS",
    model="embedding-v1",
)

db = PineconeVectorStore(
    index_name="llmops", pinecone_api_key=key, embedding=embeddings, namespace="dataset"
)

metadata_filed_info = [
    AttributeInfo(name="year", description="电影的年份", type="integer"),
    AttributeInfo(name="rating", description="电影的评分", type="float"),
    AttributeInfo(name="director", description="电影的导演", type="string"),
]

retriever = db.as_retriever()

# db.add_documents(documents)

self_query_retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=db,
    document_contents="电影的名字",
    metadata_field_info=metadata_filed_info,
    enable_limit=True,
)

# 4.检索示例
docs = self_query_retriever.invoke("查找下评分高于9.5分的电影")
print(docs)
print(len(docs))
print("===================")
base_docs = retriever.invoke("查找下评分高于9.5分的电影")
print(base_docs)
print(len(base_docs))
