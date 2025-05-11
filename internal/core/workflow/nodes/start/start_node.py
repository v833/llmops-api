from internal.core.workflow.entites.node_entity import (
    BaseNodeData,
    NodeResult,
    NodeStatus,
)
from internal.core.workflow.entites.variable_entity import (
    VARIABLE_TYPE_DEFAULT_VALUE_MAP,
)
from internal.core.workflow.entites.workflow_entity import WorkflowState
from internal.core.workflow.nodes.start.start_entity import StartNodeData

from internal.core.workflow.nodes.base_node import BaseNode
from internal.exception.exception import FailException


class StartNode(BaseNode):
    node_data: BaseNodeData

    def invoke(self, state: WorkflowState, config=None, **kwargs) -> WorkflowState:
        inputs = self.node_data.inputs

        outputs = {}

        for input in inputs:
            input_value = state["inputs"].get(input.name, None)
            if input_value is None:
                if input.required:
                    raise FailException(
                        "工作流参数生成出错，缺少必填参数: {}".format(input.name)
                    )
                else:
                    input_value = VARIABLE_TYPE_DEFAULT_VALUE_MAP[input.type]

            outputs[input.name] = input_value

        return {
            "node_results": [
                NodeResult(
                    node_data=self.node_data,
                    status=NodeStatus.SUCCESSED,
                    inputs=state["inputs"],
                    outputs=outputs,
                )
            ],
        }
