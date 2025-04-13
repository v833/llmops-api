import weaviate
from langchain_weaviate import WeaviateVectorStore
from weaviate.auth import AuthApiKey
from langchain_community.embeddings import QianfanEmbeddingsEndpoint
from langchain.retrievers import MultiQueryRetriever
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from langchain_core.runnables import RunnableMap

load_dotenv()


def format_qa_pair(question: str, answer: str) -> str:
    """格式化传递的问题+答案为单个字符串"""
    return f"Question: {question}\nAnswer: {answer}\n\n".strip()


decomposition_prompt = ChatPromptTemplate.from_template(
    "你是一个乐于助人的AI助理，可以针对一个输入问题生成多个相关的子问题。\n"
    "目标是将输入问题分解成一组可以独立回答的子问题或者子任务。\n"
    "生成与一下问题相关的多个搜索查询：{question}\n"
    "并使用换行符进行分割，输出（3个子问题/子查询）："
)

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"), temperature=0
)

decomposition_chain = (
    {"question": RunnablePassthrough()}
    | decomposition_prompt
    | llm
    | StrOutputParser()
    | (lambda x: x.strip().split("\n"))
)


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

question = "关于LLMOps应用配置的文档有哪些"
sub_questions = decomposition_chain.invoke(question)

prompt = ChatPromptTemplate.from_template(
    """这是你需要回答的问题：
---
{question}
---

这是所有可用的背景问题和答案对：
---
{qa_pairs}
---

这是与问题相关的额外背景信息：
---
{context}
---"""
)

# chain = RunnableMap(
#     {
#         "question": itemgetter("question"),
#         "qa_pairs": itemgetter("qa_pairs"),
#         "context": itemgetter("question") | retriever,
#     }
#     | prompt
#     | llm
#     | StrOutputParser()
# )
chain = (
    {
        "question": itemgetter("question"),
        "qa_pairs": itemgetter("qa_pairs"),
        "context": itemgetter("question") | retriever,
    }
    | prompt
    | llm
    | StrOutputParser()
)

# 5.循环遍历所有子问题进行检索并获取答案
qa_pairs = ""
for sub_question in sub_questions:
    answer = chain.invoke({"question": sub_question, "qa_pairs": qa_pairs})
    qa_pair = format_qa_pair(sub_question, answer)
    qa_pairs += "\n---\n" + qa_pair
    print(f"问题: {sub_question}")
    print(f"答案: {answer}")
