import weaviate
from langchain_weaviate import WeaviateVectorStore
from weaviate.auth import AuthApiKey
from langchain_community.embeddings import QianfanEmbeddingsEndpoint
from langchain_core.runnables import ConfigurableField


db = WeaviateVectorStore(
    client=weaviate.connect_to_wcs(
        cluster_url="1fhiundrq0kuto2x9gdkq.c0.us-west3.gcp.weaviate.cloud",
        auth_credentials=AuthApiKey("0gWPk59blkhPdzLcS2jy8SiUFlaKDYV0qGvQ"),
    ),
    index_name="DatasetDemo",
    text_key="text",
    embedding=QianfanEmbeddingsEndpoint(
        qianfan_ak="uexDJXSAF3qDg7tR3vkQZLOS",
        qianfan_sk="ovpeF9z5CcZleDczaFuc49AVhOjxGezS",
        model="embedding-v1",
    ),
)

# 4.转换检索器（带阈值的相似性搜索，数据为10条，得分阈值为0.5）
retriever = db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 10, "score_threshold": 0.5},
).configurable_fields(
    search_type=ConfigurableField(
        id="db_search_type",
        name="搜索类型",
        description="检索器的搜索类型",
    ),
    search_kwargs=ConfigurableField(
        id="db_search_kwargs",
        name="搜索参数",
        description="检索器的搜索参数",
    ),
)

# 5.检索结果
documents = retriever.invoke("关于配置接口的信息有哪些", config={
    "configurable": {
        "db_search_kwargs": {
            "k": 4,
        },
        # mmr可以去重
        "db_search_type": "mmr",
    }
})

print(list(document.page_content[:20] for document in documents))
print(len(documents))
