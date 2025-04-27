from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import os


class RouteQuery(BaseModel):
    """将用户查询映射到对应的数据源上"""

    datasource: Literal["python_docs", "js_docs", "golang_docs"] = Field(
        description="根据用户的问题，选择哪个数据源最相关以回答用户的问题"
    )


llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"), temperature=0
)

structured_llm = llm.with_structured_output(RouteQuery)


def choose_route(result: RouteQuery) -> str:
    """根据传递的路由结果选择不同的检索器"""
    if "python_docs" in result.datasource:
        return "chain in python_docs"
    elif "js_docs" in result.datasource:
        return "chain in js_docs"
    else:
        return "golang_docs"


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个擅长将用户问题路由到适当的数据源的专家。\n请根据问题涉及的编程语言，将其路由到相关数据源",
        ),
        ("human", "{question}"),
    ]
)
router = {"question": RunnablePassthrough()} | prompt | structured_llm | choose_route

question = """为什么下面的代码不工作了，请帮我检查下：

from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(["human", "speak in {language}"])
prompt.invoke("中文")"""

# 4.选择不同的数据库
print(router.invoke(question))
