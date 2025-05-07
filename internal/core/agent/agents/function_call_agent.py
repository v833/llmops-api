import json
import uuid
import time
from threading import Thread
from typing import Generator, override
from langchain.schema.messages import AnyMessage
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    RemoveMessage,
    ToolMessage,
)
from internal.core.agent.agents.base_agent import BaseAgent
from internal.core.agent.entities.agent_entity import (
    AgentState,
    AGENT_SYSTEM_PROMPT_TEMPLATE,
)
from internal.core.agent.entities import AgentQueueEvent, QueueEvent
from langgraph.graph import StateGraph, END
from internal.exception.exception import FailException
from langchain_core.messages import messages_to_dict


class FunctionCallAgent(BaseAgent):

    def run(
        self, query: str, history: list[AnyMessage] = None, long_term_memory: str = ""
    ) -> Generator[AgentQueueEvent, None, None]:
        if history is None:
            history = []

        agent = self._build_graph()

        thread = Thread(
            target=agent.invoke,
            args=(
                {
                    "messages": [HumanMessage(content=query)],
                    "history": history,
                    "long_term_memory": long_term_memory,
                },
            ),
        )

        thread.start()

        yield from self.agent_queue_manager.listen()

    def _build_graph(self):
        graph = StateGraph(AgentState)

        graph.add_node("long_term_memory_recall", self._long_term_memory_recall_node)
        graph.add_node("llm", self._llm_node)
        graph.add_node("tools", self._tools_node)
        graph.set_entry_point("long_term_memory_recall")
        graph.add_edge("long_term_memory_recall", "llm")
        graph.add_conditional_edges(
            "llm",
            self._tool_condition,
        )
        graph.add_edge("tools", "llm")

        agent = graph.compile()

        return agent

    def _long_term_memory_recall_node(self, state: AgentState):
        long_term_memory = ""
        if self.agent_config.enable_long_term_memory:
            long_term_memory = state["long_term_memory"]
            self.agent_queue_manager.publish(
                AgentQueueEvent(
                    id=uuid.uuid4(),
                    task_id=self.agent_queue_manager.task_id,
                    event=QueueEvent.LONG_TERM_MEMORY_RECALL,
                    observation=long_term_memory,
                )
            )
        preset_messages = [
            SystemMessage(
                AGENT_SYSTEM_PROMPT_TEMPLATE.format(
                    preset_prompt=self.agent_config.preset_prompt,
                    long_term_memory=long_term_memory,
                )
            ),
        ]

        history = state["history"]
        if isinstance(history, list) and len(history) > 0:
            if len(history) % 2 != 0:
                raise FailException("历史消息列表长度必须为偶数")

        preset_messages.extend(history)

        human_message = state["messages"][-1]
        preset_messages.append(HumanMessage(content=human_message.content))

        return {
            "messages": [RemoveMessage(id=human_message.id), *preset_messages],
        }

    def _llm_node(self, state: AgentState):
        llm = self.agent_config.llm
        if (
            hasattr(llm, "bind_tools")
            and callable(getattr(llm, "bind_tools"))
            and len(self.agent_config.tools) > 0
        ):
            llm = llm.bind_tools(self.agent_config.tools)

        gathered = None
        is_first_chunk = True
        generation_type = None
        id = uuid.uuid4()
        start_at = time.perf_counter()
        for chunk in llm.stream(state["messages"]):
            if is_first_chunk:
                gathered = chunk
                is_first_chunk = False
            else:
                gathered += chunk

            if not generation_type:
                if chunk.tool_calls:
                    generation_type = "thought"
                elif chunk.content:
                    generation_type = "message"

            # 如果生成的是消息则提交智能体消息事件
            if generation_type == "message":
                self.agent_queue_manager.publish(
                    AgentQueueEvent(
                        id=id,
                        task_id=self.agent_queue_manager.task_id,
                        event=QueueEvent.AGENT_MESSAGE,
                        thought=chunk.content,
                        messages=messages_to_dict(state["messages"]),
                        answer=chunk.content,
                        latency=(time.perf_counter() - start_at),
                    )
                )
        if generation_type == "thought":
            self.agent_queue_manager.publish(
                AgentQueueEvent(
                    id=id,
                    task_id=self.agent_queue_manager.task_id,
                    event=QueueEvent.AGENT_THOUGHT,
                    messages=messages_to_dict(state["messages"]),
                    latency=(time.perf_counter() - start_at),
                )
            )
        elif generation_type == "message":
            # 如果LLM直接生成answer则表示已经拿到了最终答案，则停止监听
            self.agent_queue_manager.stop_listen()

        return {
            "messages": [gathered],
        }

    def _tools_node(self, state: AgentState):
        tools_by_name = {tool.name: tool for tool in self.agent_config.tools}

        tool_calls = state["messages"][-1].tool_calls
        messages = []
        for tool_call in tool_calls:
            tool = tools_by_name.get(tool_call["name"])
            if tool is None:
                raise FailException(f"未找到工具{tool_call['name']}")

            id = uuid.uuid4()
            start_at = time.perf_counter()
            tool_result = tool.invoke(tool_call["args"])
            messages.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                )
            )

            event = (
                QueueEvent.AGENT_ACTION
                if tool_call["name"] != "dataset_retrieval"
                else QueueEvent.DATASET_RETRIEVAL
            )
            self.agent_queue_manager.publish(
                AgentQueueEvent(
                    id=id,
                    task_id=self.agent_queue_manager.task_id,
                    event=event,
                    observation=json.dumps(tool_result),
                    tool=tool_call["name"],
                    tool_input=tool_call["args"],
                    latency=(time.perf_counter() - start_at),
                )
            )

        return {
            "messages": messages,
        }

    @classmethod
    def _tool_condition(cls, state: AgentState):
        ai_message = state["messages"][-1]
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"
        return END
