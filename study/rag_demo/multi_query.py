import weaviate
from langchain_weaviate import WeaviateVectorStore
from weaviate.auth import AuthApiKey
from langchain_community.embeddings import QianfanEmbeddingsEndpoint
from langchain.retrievers import MultiQueryRetriever
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()
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

retriever = db.as_retriever(search_type="mmr")

multi_qwery_retriever = MultiQueryRetriever.from_llm(
    llm=ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY")),
    retriever=retriever,
)

documents = multi_qwery_retriever.invoke("关于配置接口的信息有哪些")

print(list(document.page_content[:20] for document in documents))
print(len(documents))
