from typing import Optional, Iterator
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import BaseTool
from pydantic import Field, PrivateAttr
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import StateGraph

from internal.core.workflow.entites.workflow_entity import WorkflowConfig, WorkflowState


class Workflow(BaseTool):
    _workflow_config: WorkflowConfig = PrivateAttr(None)
    _workflow: CompiledStateGraph = PrivateAttr(None)

    def __init__(self, workflow_config: WorkflowConfig, **kwargs):
        super().__init__(
            name=workflow_config.name,
            description=workflow_config.description,
            **kwargs,
        )

        self._workflow_config = workflow_config
        self._workflow = self._build_workflow()

    def _run(self, *args, **kwargs):
        return self._workflow.invoke(
            {
                "inputs": kwargs,
            }
        )

    def _build_workflow(self) -> CompiledStateGraph:
        graph = StateGraph(WorkflowState)

        return graph.compile()

    def stream(
        self, input: Input, config: Optional[RunnableConfig] = None
    ) -> Iterator[Output]:
        return self._workflow.stream(
            {
                "inputs": input,
            }
        )
