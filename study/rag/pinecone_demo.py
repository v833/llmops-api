from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import QianfanEmbeddingsEndpoint
from langchain_core.embeddings import Embeddings # Import base class
from typing import List # For type hinting

ak = 'uexDJXSAF3qDg7tR3vkQZLOS'
sk = 'ovpeF9z5CcZleDczaFuc49AVhOjxGezS'
key = 'pcsk_vTvx6_CQRdW74RPuuRnLfNZeeAFo9Q77SgDLekaUVspFVF1oZFGecPqKm3FoBmzbuZaX2'

# --- Custom Embedding Wrapper ---
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

# --- 使用包装后的 Embedding ---
embedding = QianfanFloatEmbedding(
    qianfan_ak=ak,
    qianfan_sk=sk,
    model='embedding-v1',
)

# --- 示例文本和元数据 ---
texts = [
    "笨笨是一只很喜欢睡觉的猫咪",
    "我喜欢在夜晚听音乐，这让我感到放松。",
    "猫咪在窗台上打盹，看起来非常可爱。",
    "学习新技能是每个人都应该追求的目标。",
    "我最喜欢的食物是意大利面，尤其是番茄酱的那种。",
    "昨晚我做了一个奇怪的梦，梦见自己在太空飞行。",
    "我的手机突然关机了，让我有些焦虑。",
    "阅读是我每天都会做的事情，我觉得很充实。",
    "他们一起计划了一次周末的野餐，希望天气能好。",
    "我的狗喜欢追逐球，看起来非常开心。",
]

metadatas = [
    {"source": "doc1"},
    {"source": "doc2"},
    {"source": "doc3"},
    {"source": "doc4"},
    {"source": "doc5"},
    {"source": "doc6"},
    {"source": "doc7"},
    {"source": "doc8"},
    {"source": "doc9"},
    {"source": "doc10"},
]

# --- 初始化 Pinecone 向量存储 ---
# 使用包装后的 embedding 实例
db = PineconeVectorStore(
    index_name='llmops',
    pinecone_api_key=key,
    embedding=embedding,
    namespace='dataset'
    )

# db.add_texts(texts, metadatas, namespace='dataset')

result = db.similarity_search_with_relevance_scores(
    query="我养了一只猫, 叫笨笨",
    k=3,
    namespace='dataset'
)

print(result)