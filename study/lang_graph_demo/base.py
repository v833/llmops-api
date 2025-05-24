from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, Literal
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field
import json
import dotenv

dotenv.load_dotenv()


class MultiplyInput(BaseModel):
    a: int = Field(description="第一个数字")
    b: int = Field(description="第二个数字")


@tool("multiply_tool", return_direct=True, args_schema=MultiplyInput)
def multiply(a: int, b: int) -> int:
    """将传递的两个数字相乘"""
    return a * b


llm = ChatOpenAI(model="deepseek-chat")
tools = [multiply]
llm_with_tools = llm.bind_tools(tools)


class State(TypedDict):
    messages: Annotated[list, add_messages]


def chatbot(state: State, config: dict):
    """聊天机器人节点，使用大语言模型根据传递的消息列表生成内容"""
    ai_message = llm_with_tools.invoke(state["messages"])
    return {
        "messages": [ai_message],
    }


def tool_exector(state: State, config: dict):
    """工具执行器节点，执行工具调用"""
    tool_calls = state["messages"][-1].tool_calls

    tools_by_name = {tool.name: tool for tool in tools}

    messages = []
    for tool_call in tool_calls:
        tool = tools_by_name.get(tool_call["name"])
        messages.append(
            ToolMessage(
                tool_call_id=tool_call["id"],
                content=json.dumps(tool.invoke(tool_call["args"])),
                name=tool_call["name"],
            )
        )
    return {
        "messages": messages,
    }


def route(state: State, config: dict) -> Literal["tool_exector", "__end__"]:
    """路由节点，决定消息的去向"""
    ai_message = state["messages"][-1]
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tool_exector"
    else:
        return END


graph_builder = StateGraph(State)

graph_builder.add_node("llm", chatbot)
graph_builder.add_node("tool_exector", tool_exector)

graph_builder.set_entry_point("llm")
graph_builder.add_edge("llm", route)
graph_builder.add_edge("tool_exector", "llm")

graph = graph_builder.compile()

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
