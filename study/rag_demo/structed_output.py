import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
import os

dotenv.load_dotenv()


class QAExtra(BaseModel):
    """一个问答键值对工具，传递对应的假设性问题+答案"""

    question: str = Field(description="假设性问题")
    answer: str = Field(description="假设性问题对应的答案")


llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"))

structured_llm = llm.with_structured_output(QAExtra, method="json_mode")

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "请从用户传递的query中提取出假设性的问题+答案。响应格式为JSON，并携带`question`和`answer`两个字段。",
        ),
        ("human", "{query}"),
    ]
)

chain = {"query": RunnablePassthrough()} | prompt | structured_llm

print(chain.invoke("我叫xx，我喜欢打篮球，游泳。"))
