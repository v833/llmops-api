from abc import ABC

from langchain_core.runnables import RunnableSerializable
from internal.core.workflow.entites.node_entity import BaseNodeData


class BaseNode(RunnableSerializable, ABC):
    """工作流节点基类"""

    node_data: BaseNodeData
