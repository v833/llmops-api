from typing import List
import weaviate
from langchain_weaviate import WeaviateVectorStore
from weaviate.auth import AuthApiKey
from langchain_community.embeddings import QianfanEmbeddingsEndpoint
from langchain.retrievers import MultiQueryRetriever
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain.load import dumps, loads

class RAGFusionRetriever(MultiQueryRetriever):
  k: int = 4
  
  def retrieve_documents(self, queries, run_manager):
        documents = []
        for query in queries:
            docs = self.retriever.invoke(
                query, config={"callbacks": run_manager.get_child()}
            )
            documents.append(docs)
        return documents
  
  def unique_union(self, documents):
      fused_result = {}
  
      for docs in documents:
        for rank, doc in enumerate(docs):
          doc_str = dumps(doc)

          if doc_str not in fused_result:
            fused_result[doc_str] = 0

          fused_result[doc_str] += 1 / (rank + 60)

      reranked_results = [
        (loads(doc), score) for doc, score in sorted(fused_result.items(),key=lambda x: x[1], reverse=True)
      ]

      return [item[0] for item in reranked_results[:self.k]]
  

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

multi_qwery_retriever = RAGFusionRetriever.from_llm(
    llm=ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY")),
    retriever=retriever,
)

documents = multi_qwery_retriever.invoke("关于配置接口的信息有哪些")

print(list(document.page_content[:20] for document in documents))
print(len(documents))
