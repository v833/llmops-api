from abc import ABC
from typing import Type

from internal.core.workflow.entites.node_entity import BaseNodeData

from langchain_core.runnables import RunnableSerializable


class BaseNode(RunnableSerializable, ABC):
    _node_data_cls: type[BaseNodeData]
    node_data: BaseNodeData

    def __init__(self, *args, node_data: BaseNodeData, **kwargs):
        super().__init__(*args, node_data=self._node_data_cls(**node_data), **kwargs)
