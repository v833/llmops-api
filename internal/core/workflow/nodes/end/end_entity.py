from pydantic import Field
from internal.core.workflow.entites.node_entity import BaseNodeData
from internal.core.workflow.entites.variable_entity import VariableEntity


class EndNodeData(BaseNodeData):
    outputs: list[VariableEntity] = Field(default_factory=list)
