from langchain_core.pydantic_v1 import Field

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity


class StartNodeData(BaseNodeData):
    """开始节点数据"""

    inputs: list[VariableEntity] = Field(default_factory=list)  # 开始节点的输入变量信息
