from typing import Any, Optional, Iterator
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr, create_model
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph import StateGraph
from internal.core.workflow.entites.node_entity import NodeType
from internal.core.workflow.entites.variable_entity import VARIABLE_TYPE_MAP
from internal.core.workflow.entites.workflow_entity import WorkflowConfig, WorkflowState
from internal.core.workflow.nodes import StartNode, EndNode

NodeClasses = {
    NodeType.START: StartNode,
    NodeType.END: EndNode,
}


class Workflow(BaseTool):
    _workflow_config: WorkflowConfig = PrivateAttr(None)
    _workflow: CompiledStateGraph = PrivateAttr(None)

    def __init__(self, workflow_config: WorkflowConfig, **kwargs):
        super().__init__(
            name=workflow_config.name,
            description=workflow_config.description,
            args_schema=self._build_args_schema(workflow_config),
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

    @classmethod
    def _build_args_schema(cls, workflow_config: WorkflowConfig) -> type[BaseModel]:
        """构建输入参数结构体"""
        # 1.提取开始节点的输入参数信息
        fields = {}
        inputs = next(
            (
                node.inputs
                for node in workflow_config.nodes
                if node.node_type == NodeType.START
            ),
            [],
        )

        # 2.循环遍历所有输入信息并创建字段映射
        for input in inputs:
            field_name = input.name
            field_type = VARIABLE_TYPE_MAP.get(input.type, str)
            field_required = input.required
            field_description = input.description

            fields[field_name] = (
                field_type if field_required else Optional[field_type],
                Field(description=field_description),
            )

        # 3.调用create_model创建一个BaseModel类，并使用上述分析好的字段
        return create_model("DynamicModel", **fields)

    def _build_workflow(self) -> CompiledStateGraph:
        graph = StateGraph(WorkflowState)

        nodes = self._workflow_config.nodes
        edges = self._workflow_config.edges

        for node in nodes:
            node_flag = f"{node.node_type.value}_{node.id}"
            if node.node_type == NodeType.START:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.START](node_data=node),
                )
            elif node.node_type == NodeType.END:
                graph.add_node(
                    node_flag,
                    NodeClasses[NodeType.END](node_data=node),
                )
            else:
                pass

        for edge in edges:
            graph.add_edge(
                f"{edge.get('source_type')}_{edge.get('source')}",
                f"{edge.get('target_type')}_{edge.get('target')}",
            )

            if edge.get("source_type") == NodeType.START:
                graph.set_entry_point(f"{edge.get('source_type')}_{edge.get('source')}")
            if edge.get("target_type") == NodeType.END:
                graph.set_finish_point(
                    f"{edge.get('target_type')}_{edge.get('target')}"
                )

        return graph.compile()

    def stream(
        self, input: Input, config: Optional[RunnableConfig] = None
    ) -> Iterator[Output]:
        return self._workflow.stream(
            {
                "inputs": input,
            }
        )
