from typing import override
from langchain.schema.messages import AnyMessage
from langchain_core.messages import HumanMessage
from internal.core.agent.agents.base_agent import BaseAgent
from internal.core.agent.entities.agent_entity import AgentState
from langgraph.graph import StateGraph, END


class FunctionCallAgent(BaseAgent):

    def run(
        self, query: str, history: list[AnyMessage] = None, long_term_memory: str = ""
    ):
        if history is None:
            history = []

        agent = self._build_graph()

        return agent.invoke(
            {
                "messages": [HumanMessage(content=query)],
                "history": history,
                "long_term_memory": long_term_memory,
            },
        )

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
        pass

    def _llm_node(self, state: AgentState):
        pass

    def _tools_node(self, state: AgentState):
        pass

    @classmethod
    def _tool_condition(cls, state: AgentState):
        ai_message = state["messages"][-1]
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"
        return END
