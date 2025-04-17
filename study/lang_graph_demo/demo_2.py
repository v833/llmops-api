from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
import datetime

model = ChatOpenAI(model="deepseek-chat")


@tool("get_time", description="获取当前时间")
def get_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


tools = [get_time]

checkpointer = MemorySaver()
config = {"configurable": {"thread_id": 1}}
agent = create_react_agent(model=model, tools=tools, checkpointer=checkpointer)

state = agent.invoke(
    {
        "messages": [("human", "你好, 我叫wq")],
    },
    config=config,
)
for message in state["messages"]:
    print("消息类型: ", message.type)
    print("消息内容: ", message.content)

state2 = agent.invoke({"messages": [("human", "你知道我叫什么吗?")]}, config=config)

for message in state2["messages"]:
    print("消息类型: ", message.type)
    print("消息内容: ", message.content)
