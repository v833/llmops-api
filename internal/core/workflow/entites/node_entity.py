from enum import Enum
from uuid import UUID
from typing import Any

from pydantic import BaseModel, Field

from internal.core.workflow.entites.variable_entity import VariableEntity


class NodeType(str, Enum):
    """节点类型枚举"""

    START = "start"
    LLM = "llm"
    TOOL = "tool"
    CODE = "code"
    DATASET_RETRIEVAL = "dataset_retrieval"
    HTTP_REQUEST = "http_request"
    TEMPLATE_TRANSFORM = "template_transform"
    END = "end"


class BaseNodeData(BaseModel):
    id: UUID
    title: str = ""
    description: str = ""

    class Config:
        allow_population_by_field_name = True  # 允许通过字段名进行赋值

    node_type: NodeType
    inputs: list[VariableEntity] = Field(default_factory=list)
    outputs: list[VariableEntity] = Field(default_factory=list)


class NodeStatus(str, Enum):
    """节点运行状态枚举类"""

    RUNNING = "running"
    SUCCESSED = "successed"
    FAILED = "failed"


class NodeResult(BaseModel):
    node_data: BaseNodeData
    status: NodeStatus = NodeStatus.RUNNING
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    error: str = ""
