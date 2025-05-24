from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field
import json
import dotenv

dotenv.load_dotenv()


class MultiplyInput(BaseModel):
    a: int = Field(description="第一个数字")
    b: int = Field(description="第二个数字")


@tool("multiply_tool", args_schema=MultiplyInput)
def multiply(a: int, b: int) -> int:
    """将传递的两个数字相乘"""
    return a * b


llm = ChatOpenAI(model="deepseek-chat")
tools = [multiply]


graph = create_react_agent(
    model=llm,
    tools=tools,
)

state = graph.invoke(
    {
        "messages": [("human", "你好，我想计算 2 * 3")],
    }
)

for message in state["messages"]:
    print("消息类型: ", message.type)
    if hasattr(message, "tool_calls") and len(message.tool_calls) > 0:
        print("工具调用参数: ", message.tool_calls)
    print("消息内容: ", message.content)
    print("=====================================")
