from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState
from langchain_core.messages import RemoveMessage, AIMessage
import dotenv

dotenv.load_dotenv()

llm = ChatOpenAI(model="deepseek-chat")


def chat_llm(state, config):
    """聊天机器人节点，使用大语言模型根据传递的消息列表生成内容"""
    ai_message = llm.invoke(state["messages"])
    return {
        "messages": [ai_message],
    }


def remove_llm(state, config):
    fitst_message = state["messages"][0]
    return {"messages": [RemoveMessage(id=fitst_message.id)]}


def update_llm(state, config):
    last_message = state["messages"][-1]
    return {
        "messages": [
            AIMessage(
                id=last_message.id,
                content="我已经更新了消息" + last_message.content,
            )
        ]
    }


graph_builder = StateGraph(MessagesState)

graph_builder.add_node("chat_llm", chat_llm)
graph_builder.add_node("remove_llm", remove_llm)
graph_builder.add_node("update_llm", update_llm)

graph_builder.set_entry_point("chat_llm")
graph_builder.add_edge("chat_llm", "remove_llm")
graph_builder.add_edge("remove_llm", "update_llm")

graph = graph_builder.compile()

state = graph.invoke(
    {
        "messages": [
            {
                "type": "human",
                "content": "你好，我想计算 2 * 3",
            }
        ],
    }
)


for message in state["messages"]:
    print("消息类型: ", message.type)
    if hasattr(message, "tool_calls") and len(message.tool_calls) > 0:
        print("工具调用参数: ", message.tool_calls)
    print("消息内容: ", message.content)
    print("=====================================")
