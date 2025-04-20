from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.prebuilt import ToolNode
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
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


def chatbox(state: MessagesState, config: dict):
    """聊天机器人节点，使用大语言模型根据传递的消息列表生成内容"""
    ai_message = llm_with_tools.invoke(state["messages"])
    return {
        "messages": [ai_message],
    }


def route(state: MessagesState, config: dict) -> Literal["tools", "__end__"]:
    """动态选择工具执行亦或者结束"""
    # 1.获取生成的最后一条消息
    ai_message = state["messages"][-1]
    # 2.检测消息是否存在tool_calls参数，如果是则执行`工具路由`
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    # 3.否则生成的内容是文本信息，则跳转到结束路由
    return END


graph_builder = StateGraph(MessagesState)

graph_builder.add_node("chatbox", chatbox)
graph_builder.add_node("tools", ToolNode(tools=tools))

graph_builder.set_entry_point("chatbox")
graph_builder.add_edge("tools", "chatbox")
graph_builder.add_conditional_edges("chatbox", route)


checkpointer = MemorySaver()
config = {"configurable": {"thread_id": 1}}
graph = graph_builder.compile(checkpointer=checkpointer, interrupt_before=["tools"])


state = graph.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "请将 2 和 3 相乘",
            }
        ]
    },
    config=config,
)

print(state)

# 6.进行人机交互
if (
    hasattr(state["messages"][-1], "tool_calls")
    and len(state["messages"][-1].tool_calls) > 0
):
    print("现在准备调用工具: ", state["messages"][-1].tool_calls)
    human_input = input("如果需要执行工具请输入yes，否则请输入no: ")
    if human_input.lower() == "yes":
        print(graph.invoke(None, config)["messages"][-1].content)
    else:
        print("图程序执行完毕")
