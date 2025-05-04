## LCEL 与 AgentExecutor 的局限性

有向无环图 链式应用在处理复杂、动态的对话流程时存在着一些局限性：

1. 线性流程：链通常是线性的，这意味着它们只能按照预定义的顺序执行步骤，这种线性结构限制了在对话中进行动态路由和条件分支的能力。
2. 状态管理：链在处理多轮对话时，状态管理变得非常复杂，每次调用链时，都需要手动传递和更新状态，增加了代码的复杂性和出错的可能性。
3. 工具集成：虽然链可以调用外部工具，但在链的内部结构中集成和协调多个工具的使用并不直观，尤其是在需要根据对话上下文动态选择工具时。

AgentExecutor 的诞生解决了 LCEL 的部分缺陷，它允许智能体根据输入动态选择工具和操作，尽管 AgentExecutor 提供了一定的灵活性，但它也存在着一些局限性：

1. 复杂性：AgentExecutor 的配置和使用相对复杂，尤其是在处理复杂的对话流程和多轮对话时，需要手动管理智能体的状态和工具调用，这增加了开发的难度。
2. 动态路由：AgentExecutor 虽然支持动态选择工具，但在处理复杂的条件分支和动态路由时，仍然不够灵活。缺乏一种直观的方式来定义和执行复杂的对话流程。
3. 状态持久性：AgentExecutor 在处理长时间运行的对话时，缺乏内置的状态持久性机制。每次对话重启时，都需要从头开始，无法恢复之前的对话状态。
4. 过度封装：AgentExecutor 要求被包装的 Agent 必须符合特定的要求才能使用，例如 输入变量固定、输入prompt固定、解析器固定 等，想要二次开发 AgentExecutor 难度非常大。
5. 黑盒不可控：在构建复杂 Agent 时无法修改工具的使用顺序，无法在执行过程中添加人机交互。

## LangGraph 介绍与功能
LangGraph 是一个构建具有 状态、多角色 应用程序的库，用于创建智能体和多智能体工作流，与其他 LLM 框架相比，LangGraph 提供了以下核心优势：循环、可控制性和持久性。LangGraph 允许定义设计循环、条件判断的流程，这对于高级 Agent 非常重要，这和传统的有向无换图（DAG）解决方案区分开。

对比 LCEL 表达式，LangGraph 的主要功能：
- 循环和分支：在 LLM/Agent 应用程序中使用便捷的方式实现循环和条件语句，而无需配置额外的程序。
- 持久化：在图的每个步骤之后自动保存状态，在运行的任意一个阶段都支持暂停和恢复图执行，以支持错误恢复、人机交互工作流、时间旅行等。
- 人机交互：中断图的执行以批准或者编辑状态计划去执行下一计划。
- 流支持：图结构的每个节点都支持流式输出（包括 token 流式输出）。
- 与LangChain集成：LangGraph 可以和 LangChain 和 LangSmith 无缝集成

在一个最基础 LangGraph 应用程序中，涵盖了 3 种基本组件：
1. 状态：状态是图应用程序处理与交互的基础，是图中所有 节点 和 边 的输入，它可以是一个 dict(字典) 或者 Pydantic模型，在 LangGraph 中，状态包括 图的模式(数据结构) 以及如何更新状态的 归纳函数，如果没有设置 归纳函数，则每次节点都会覆盖 状态 的原始数据。
2. 节点：节点通常是 Python 函数（同步或异步），其中节点函数的第一个参数是 state(状态)，第二个参数是 config(Runnable运行的配置)，节点函数的返回值一般都是 状态，整个图的起点被称为开始节点，最后的终点被称为结束节点。
3. 边：边在图中定义了路由逻辑，即不同节点之间是如何传递的，传递给谁，以及图节点从哪里开始，从哪里结束，并且一个节点可以设置多条边，如果有多条边，则下一条边连接的所有节点都会并行运行。

在 LangGraph 中，无论多么复杂的项目，都可以拆分成对应的 6 个步骤，只需按照这 6 个步骤来执行即可：

1. 初始化大语言模型和工具（ChatOpenAI、tools）。
2. 用状态初始化图架构（StateGraph 状态图）。
3. 为图定义每一个节点（add_node 函数为图添加节点）。
4. 定义图的起点、终点和节点边（add_edge 函数为图添加边）。
5. 编译图架构为 Runnable 可运行组件（graph.compile 函数编译图）。
6. 调用编译后的 Runnable 可运行组件执行图（graph.invoke 函数调用图）。

```
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated

import dotenv

dotenv.load_dotenv()
llm = ChatOpenAI(model="deepseek-chat")


class State(TypedDict):
    messages: Annotated[list, add_messages]
    use_name: str


def chatbot(state: State, config: dict):
    """聊天机器人节点，使用大语言模型根据传递的消息列表生成内容"""
    ai_message = llm.invoke(state["messages"])
    return {
        "messages": [ai_message],
        "use_name": "chatbox",
    }


graph_builder = StateGraph(State)

graph_builder.add_node("llm", chatbot)

graph_builder.add_edge(START, "llm")
graph_builder.add_edge("llm", END)

graph = graph_builder.compile()

print(
    graph.invoke(
        {
            "messages": [("human", "你好，你是谁，我叫慕小课，我喜欢打篮球游泳")],
            "use_name": "graph",
        }
    )
)

```

## 条件边与循环流程实现工具调用Agent

在 LangChain 中，边 定义了节点之间是如何工作的，以及图结构从哪里开始，从哪里结束，在 LangGraph 中，边的种类有 4 种：

- 普通边：直接从一个节点到下一个节点。
- 条件边：调用一个函数来确定下一个需要跳转的节点。
- 入口边：用户输入到达时首先调用的节点，即确定 图结构 的开始节点。
- 条件入口点：调用一个函数来确定用户输入到达时首先调用的节点，即通过函数来确定 图结构 的开始节点。

普通边 可以直接使用 add_edge() 函数即可，如果想为某个节点添加 条件边，可以使用 add_conditional_edge() 函数，该函数的返回值为字符串或者列表，代表需要执行节点的名称（一个或多个），函数共有 4 个参数，其中前 2 个参数为必填：

- source：条件边的起始节点名称，该节点运行结束后会执行条件边。
- path：确定下一个节点是什么的可运行对象或者函数。
- path_map：可选参数，类型为一个字典，用于表示 返回的path和 节点名称 的映射关系，如果不设置的话，path 的返回值应该是 节点名称。
- then：可选参数，在执行 path 节点之后统一选择节点，通过该设置就不需要为后续的每一个节点都设置一个统一的关联节点。
对于 循环流程 而言，在 LangGraph 并没有单独设置函数，只需要通过 add_edge() 将两个节点串联起来即可。

注意下，对于 循环流程，一般都会有一个 条件边 用于跳出循环，否则 LangGraph 框架会检测到没有跳出循环的条件，应用程序会崩溃，并且极大消耗系统资源。

```
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, Literal
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field
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
graph_builder.add_conditional_edges("llm", route)
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

```

## 并行调用边使用示例
在 LangGraph 中，一个节点可以同时连接多条边，被连接到的所有节点全部都会并行执行，直到再次关联到一起，或者图运行结束。
例如下方左右有两个并行运行流程，其中左侧的两个并行节点均有连接到 END 节点，右侧的只有一个，但是最终结果是一模一样的，只要不把 状态 看成是 传递，而是整个图的全局变量，每个节点执行的都是 修改 操作即可。

![图片](assets/IMG_4.png)

## 删除/更新信息

```
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

```

## 过滤与修剪消息

在 LangGraph 中 状态 可以很便捷管理整个过程中产生的所有消息信息，但是随着持续对话，亦或者图结构组件的增加，对话历史会不断累积，并占用越来越多的上下文窗口，这通常是不可取的，因为它会导致对 LLM 的调用变得非常昂贵和耗时，并降低 LLM 生成内容的正确性，所以在 LangGraph 中一般还需要对消息进行过滤和修剪。

过滤/修剪 一般不会更改 状态，而是在调用 LLM 时，只传递特定条数的消息或者按照 token长度 进行修剪。

例如使用 过滤消息 可以单独创建一个函数（非节点），在调用 LLM 前，对消息进行过滤

在 LangChain 中对于该需求还封装了特定的函数 trim_messages，该函数的参数如下：

- messages：需要修剪的消息列表。
- max_tokens：修剪消息的最大 Token 数。
- strategy：修剪策略，first 代表从前往后修剪消息，last 代表从后往前修剪消息，默认为 last。
- token_counter：计算 Token 数的函数，或者传递大语言模型（使用大语言模型的 .get_num_tokens_from_messages() 计算 Token 数）。
- allow_partial：如果只能拆分消息的一部分，是否拆分消息，默认为 False，拆分可以分成多种，一种是消息文本单独拆分，另外一种是如果设置了 n，一次性返回多条消息，针对消息的拆分。
- end_on：修剪消息结束的类型，如果执行，则在这种类型的最后一次出现时将被忽略，类型为列表或者单个值（支持传递消息的类型字符串，例如：system、human、ai、tool 等，亦或者传递消息类）。
- start_on：修剪消息开始的类型，如果执行，则在这种类型的最后一次出现时将被忽略，类型为列表或者单个值（支持传递消息的类型字符串，例如：system、human、ai、tool 等，亦或者传递消息类）。
- include_system：是否保留系统消息，只有在 strategy="last" 时设置才有效。
- text_splitter：文本分割器，默认为空，当设置 allow_partial=True 时才有用，用于对某个消息类型中的大文本进行分割。

```
llm = ChatOpenAI(model="gpt-4o-mini")

update_messages = trim_messages(
    messages,
    max_tokens=80,
    token_counter=llm,
    strategy="first",
    end_on="human",
    allow_partial=False,
    text_splitter=RecursiveCharacterTextSplitter(),
)
```

## 检查点与线程
在 LCEL 表达式构建的链应用中，我们将 Memory组件 通过 .with_listen() 函数绑定到整个链的 运行结束生命周期 上，从而去实现链记忆功能的自动管理，在 LangGraph 中也有类似的功能，不过该功能是 检查点，在编程中 检查点 通常用于记录或标记程序在某个阶段的 状态，以便在程序运行过程中出现问题时，可以回溯到特定的状态，亦或者在图执行的过程中将任意一个节点的状态进行保存。

理解 检查点 其实很简单，想象一下你在玩一个需要多个任务的游戏，比如一个冒险游戏，你的角色需要完成许多关卡和任务。如果你在某个关卡中遇到困难或游戏崩溃，你不想从游戏的开头重新开始。于是，游戏就会在你完成每个关卡后保存一个 检查点/存档点，这样你就可以从不同 检查点/存档点 重新启动游戏继续玩。

在 LangGraph 中，持久化使用的就是 检查点，并且除了这个功能，每个 检查点 还和 线程ID 有关，检查点 存储的并不是整个图结构应用程序的 节点状态，而是存储 特定线程 的 数据状态，这是因为 LangGraph 在设计的时候就考虑到一个应用的多次独立对话功能。

就好比游戏存档中，每个家庭成员玩同一款游戏，可以保留独属于自己的不同存档，通过不同的 线程 和 检查点 实现共用一套程序，并实现完全隔离

在没有设置 检查点 与 线程 的时候，图应用程序每次运行都会管理新的 数据状态，并不会持久化，要想使用 检查点 来为图提供持久化记忆，操作技巧也非常简单，共两步：

1. 实例化一个检查点，例如 AsyncSqliteSaver 或者 MemorySaver()，亦或者自定义检查点。
2. 在图编译的时候传递检查点，例如 compile(checkpointer=my_checkpointer)。
接下来在和图程序交互时传递 config，并配置 thread_id 即可记住以往的历史记忆/存档

```
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

```

## 人在环路与断点

人在环路（Human-in-the-loop，简称 HIL）交互对于 Agent 系统至关重要，特别是在一些特定领域的 Agent 中，需要经过人类的允许或者指示才能进入下一步（例如某些敏感或者重要操作），而 HIL 最重要的部分就是 断点。

断点 建立在 LangGraph 检查点之上，检查点在每个节点执行后保存图的状态，并且 检查点 可以使得图执行可以特定点暂停，等待人为批准，然后从最后一个检查点恢复执行。

通过流程图很容易可以知道，要想实现 断点 与 人机交互，其实要做的事情很简单：

1. 在图中设置 断点，这样图结构应用程序才只可以知道在哪个节点中断；
2. 针对人类的交互进行判断，执行相应的操作，恢复执行，亦或者更换执行；

在 LangGraph 中可以通过在 .compile() 编译的时候传递 interrupt_before(前置断点) 或者 interrupt_after(后置断点)，这样在图结构程序执行到 特定的节点 时就会暂停执行，等待其他操作（例如人类提示，修改状态等）。

如果需要恢复图执行，只需要再次调用 invoke/stream 等，并传递 inputs=None，传递输入为 None 意味着像中断没有发生一样继续执行，基于这个思路就可以实现让人类干预图的执行。

```
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

```

如果在二次执行 invoke/stream 的时候传递的并不是 None，而是对应的状态，则会对状态进行更新然后继续后续的操作，但是需要注意下，在这里额外更新状态要确保消息列表符合大语言模型的消息列表规范，避免发生错误，也尽可能不使用这种带有困惑性的方式。

## 在图结构上更新对应状态

在 LangGraph 的图结构上，除了能通过 节点 更新 数据状态，还可以在图的外部通过调用图的 get_state() 与 update_state() 的方式来实现对数据状态的更新（特定线程下），并且 get_state() 和 update_state() 功能必须在 检查点 模式下才支持。

```
graph_state = graph.get_state(config)
tool_message = ToolMessage(
    # id是告诉归纳函数我和原始数据重复了，请直接覆盖
    id=graph_state[0]["messages"][-1].id,
    # 告诉大语言模型工具调用id，这里的工具调用id是让大语言模型知道这条消息是和哪个函数关联
    tool_call_id=graph_state[0]["messages"][-2].tool_calls[0]["id"],
    name=graph_state[0]["messages"][-2].tool_calls[0]["name"],
    content=“xxx”
)
print("下一个步骤:", graph_state[1])
graph.update_state(config, {"messages": [tool_message]})
print(graph.invoke(None, config)["messages"][-1].content)

```

## 子图结构与应用场景

对于一些更加复杂的系统，子图是一个非常有用的设计原则。使用子图允许在图的不同部分创建和管理不同的状态，这样可以轻松利用 LangGraph 实现类似 多智能体 亦或者 AI工作流 之类的功能，每个功能之间相互独立隔离，最后组装成一个大型复杂应用。

大家如果有使用过 Dify、Coze 等 AI 应用开发平台的 工作流，亦或者是 MetaGPT、AutoGPT、BabyAGI 等智能体框架，在这些功能下就涉及到了 多智能体 亦或者 多Agent应用 的相互协作与组成

LangGraph 的节点可以是任意的 Python 函数或者是 Runnable可运行组件，并且 图程序 经过编译后就是一个 Runnable可运行组件，所以我们可以考虑将其中一个 图程序 作为另外一个 图程序 的节点，这样就变相在 LangGraph 中去实现子图，从而将一些功能相近的节点单独组装成图，单独进行状态的管理。

而创建 子图 最核心的部分要认识到 图 之间的信息传递，入口图 是父级，两个子图都被定义成 入口图 的节点，并且两个子图都继承了父级 入口图 的状态，并且每个子图都可以拥有自己的私有状态，任何想传回父级 入口图 的值，只需要在入口图中定义即可

另外需要注意的是，如果定义了 多边，那么必须定义 归纳函数，因为多边的执行是 并行的，如果不定义归纳函数，数据会直接覆盖，由于并行的顺序是不确定的，如果不定义 归纳函数，数据可能会出现相互覆盖的问题，实际上在 LangGraph 编译的过程中，如果一个图有多边并行的情况，并且没有为每个字段都定义 归纳函数，会直接抛出错误。

### LangGraph 实现示例

例如我们实现一个 营销智能体，其功能为 根据用户传递的原始问题生成一篇【直播带货】脚本，一篇【小红书推广】文案，在这里用户传递一段原始 Prompt，会调用两个 Agent 智能体并行完成各自的任务，最后再进行合并输出。

针对这类需求，我们可以使用 单图结构 来构建，也可以创建 多图结构 来构建，更推荐使用 多图结构，其优势也非常明显：
1. 多图结构状态设计更简单，不用一次性考虑所有 Agent 智能体的状态，可以每个智能体单独管理自己的状态。
2. 多图结构更易于扩展，后续需要添加多一个 百度SEO推广文案Agent，只需添加多一个节点即可，程序无需大量调整。

```
from typing import TypedDict, Any, Annotated

import dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

dotenv.load_dotenv()


class MultiplyInput(BaseModel):
    a: int = Field(description="第一个数字")
    b: int = Field(description="第二个数字")


@tool("multiply_tool", args_schema=MultiplyInput)
def multiply(a: int, b: int) -> int:
    """将传递的两个数字相乘"""
    return a * b


llm = ChatOpenAI(model="deepseek-chat", temperature=0.0)


def reduce_str(left: str | None, right: str | None) -> str:
    if right is not None and right != "":
        return right
    return left


class AgentState(TypedDict):
    query: Annotated[str, reduce_str]  # 原始问题
    live_content: Annotated[str, reduce_str]  # 直播文案
    xhs_content: Annotated[str, reduce_str]  # 小红书文案


class LiveAgentState(AgentState):
    """直播文案智能体状态"""

    messages: Annotated[list[AnyMessage], add_messages]


class XHSAgentState(AgentState):
    """小红书文案智能体状态"""

    pass


def chatbot_live(state: LiveAgentState, config: RunnableConfig) -> Any:
    """直播文案智能体聊天机器人节点"""
    # 1.创建提示模板+链应用
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个拥有10年经验的直播文案专家，请根据用户提供的产品整理一篇直播带货脚本文案",
            ),
            ("human", "{query}"),
            ("placeholder", "{chat_history}"),
        ]
    )
    chain = prompt | llm.bind_tools([multiply])

    # 2.调用链并生成ai消息
    ai_message = chain.invoke(
        {"query": state["query"], "chat_history": state["messages"]}
    )

    return {
        "messages": [ai_message],
        "live_content": ai_message.content,
    }


live_agent_graph = StateGraph(LiveAgentState)

live_agent_graph.add_node("chatbot_live", chatbot_live)
live_agent_graph.add_node("tools", ToolNode([multiply]))

live_agent_graph.set_entry_point("chatbot_live")
live_agent_graph.add_conditional_edges("chatbot_live", tools_condition)
live_agent_graph.add_edge("tools", "chatbot_live")


def chatbot_xhs(state: XHSAgentState, config: RunnableConfig) -> Any:
    """小红书文案智能体聊天节点"""
    # 1.创建提示模板+链
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个小红书文案大师，请根据用户传递的商品名，生成一篇关于该商品的小红书笔记文案，注意风格活泼，多使用emoji表情。",
            ),
            ("human", "{query}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    # 2.调用链并生成内容更新状态
    return {"xhs_content": chain.invoke({"query": state["query"]})}


xhs_agent_graph = StateGraph(XHSAgentState)

xhs_agent_graph.add_node("chatbot_xhs", chatbot_xhs)

xhs_agent_graph.set_entry_point("chatbot_xhs")
xhs_agent_graph.set_finish_point("chatbot_xhs")


def parallel_node(state: AgentState, config: RunnableConfig) -> Any:
    return state


agent_graph = StateGraph(AgentState)
agent_graph.add_node("parallel_node", parallel_node)
agent_graph.add_node("live_agent", live_agent_graph.compile())
agent_graph.add_node("xhs_agent", xhs_agent_graph.compile())

agent_graph.set_entry_point("parallel_node")
agent_graph.add_edge("parallel_node", "live_agent")
agent_graph.add_edge("parallel_node", "xhs_agent")

agent_graph.set_finish_point("live_agent")
agent_graph.set_finish_point("xhs_agent")

# 4.编译入口图
agent = agent_graph.compile()

# 5.执行入口图并打印结果
state = agent.invoke({"query": "潮汕牛肉丸"})

```


## LangGraph 两种流式模式

在 LangGraph 中，编译后的 图程序 也是一个 Runnable可运行组件，并支持多种流式模式输出，和 LLM 使用流式模式输出一个一个词不一样，在 LangGraph 中，流式响应每次输出的都是一个节点的 数据状态，在 LangGraph 中流式模式有两种：

- values：此流式模式返回图的值，这是每个节点调用后图的 完整状态（总量）；
- updates：此流式模式返回图的更新，这是每个节点调用后图的 状态的更新（增量）；

要想使用流式模式非常简单，在调用 stream() 函数时，传递 stream_mode 参数即可配置不同的流式响应模式