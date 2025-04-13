from typing import List
import weaviate
from langchain_weaviate import WeaviateVectorStore
from weaviate.auth import AuthApiKey
from langchain_community.embeddings import QianfanEmbeddingsEndpoint
from langchain_core.retrievers import BaseRetriever
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models import BaseLanguageModel

# 加载 .env 文件
load_dotenv()


class HYDERetriever(BaseRetriever):
    retriever: BaseRetriever
    llm: BaseLanguageModel

    def _get_relevant_documents(self, query, *, run_manager):

        prompt = ChatPromptTemplate.from_template(
            "请写一篇字数不超过200字的科学论文来回答这个问题 \n" "问题: {question}\n"
        )

        # 2.构建HyDE混合策略检索链
        chain = (
            {"question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
            | self.retriever
        )

        return chain.invoke(query)


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

hyde_retriever = HYDERetriever(
    llm=ChatOpenAI(
        model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY")
    ),
    retriever=retriever,
)

documents = hyde_retriever.invoke("关于LLMOps应用配置的文档有哪些？")
print(documents)
print(len(documents))
