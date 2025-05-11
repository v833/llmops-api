from typing import Any, Annotated, TypedDict

from pydantic import BaseModel, Field

from internal.core.workflow.entites.node_entity import BaseNodeData, NodeResult


def _process_dict(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left = left or {}
    right = right or {}

    return {**left, **right}


def _process_node_results(
    left: list[NodeResult], right: list[NodeResult]
) -> list[NodeResult]:
    left = left or []
    right = right or []

    return left + right


class WorkflowConfig(BaseModel):
    name: str = "工作流名称, 必须是英文"
    description: str = "工作流描述, 用户告知LLM什么时候需要调用工作流"
    nodes: list[BaseNodeData] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)


class WorkflowState(TypedDict):
    inputs: Annotated[dict[str, Any], _process_dict]
    outputs: Annotated[dict[str, Any], _process_dict]
    node_results: Annotated[list[NodeResult], _process_node_results]
